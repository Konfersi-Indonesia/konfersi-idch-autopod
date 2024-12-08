#!/bin/bash

CONFIG_FILE=${1:-transfer-config.yaml}

# Function to parse YAML file and get the value of a key
parse_yaml() {
  local yaml_file=$1
  local key=$2
  yq eval ".${key}" "$yaml_file"
}

# Check if the required command-line tools are available
command -v rclone > /dev/null || { echo "rclone is required but not installed."; exit 1; }
command -v yq > /dev/null || { echo "yq (YAML parser) is required but not installed."; exit 1; }

# Load configuration
echo "Loading configuration from ${CONFIG_FILE}..."
DRIVER=$(parse_yaml "$CONFIG_FILE" 'download.driver')
TARGET_DOWNLOAD=$(parse_yaml "$CONFIG_FILE" 'download.target')
FILES_DOWNLOAD=$(yq eval '.download.files | join(" ")' "$CONFIG_FILE")
LOG_DOWNLOAD=$(parse_yaml "$CONFIG_FILE" 'download.log')

export EXTRACT_TARGET=$(parse_yaml "$CONFIG_FILE" 'extract.target')
export EXTRACT_LOG=$(parse_yaml "$CONFIG_FILE" 'extract.log')

FILES_EXTRACT=$(yq eval '.extract.files | join(" ")' "$CONFIG_FILE")
AUTO_DELETE=$(parse_yaml "$CONFIG_FILE" 'extract.auto_delete')

DOWNLOAD_ENABLED=$(parse_yaml "$CONFIG_FILE" 'download.enable')
if [ "$DOWNLOAD_ENABLED" == "true" ] || [ -z "$DOWNLOAD_ENABLED" ]; then
    DOWNLOAD_ENABLED=true
else
    DOWNLOAD_ENABLED=false
fi

EXTRACT_ENABLED=$(parse_yaml "$CONFIG_FILE" 'extract.enable')
if [ "$EXTRACT_ENABLED" == "true" ] || [ -z "$EXTRACT_ENABLED" ]; then
    EXTRACT_ENABLED=true
else
    EXTRACT_ENABLED=false
fi

# Function to download files
download_files() {
    echo "Starting the download process..."

    # Create a temporary file to store the list of files to be downloaded
    temp_file_list=$(mktemp)

    # Loop through all files and check if they need to be added to the temporary list
    for file in $FILES_DOWNLOAD; do
        
        # Check if the file has an asterisk symbol (*)
        if [[ "$file" == *\** ]]; then
            # Use rclone ls to check the remote directory for the file pattern
            result=$(rclone ls "$DRIVER:" --include "$file")
            
            # Loop through each result of rclone ls
            while IFS= read -r line; do
                # Extract the filename from the rclone result (assuming it's in the second column)
                filename=$(echo "$line" | awk '{print $2}')
                
                # Check if the filename is not already in the temp file list
                if ! grep -Fxq "$filename" "$temp_file_list"; then
                    # Append the filename to the temporary file list
                    echo "$filename" >> "$temp_file_list"
                fi
            done <<< "$result"
        else
            # If the file does not have an asterisk, directly append it to the temp file list
            echo "$file" >> "$temp_file_list"
        fi
    done

    echo "Files to download:"
    cat $temp_file_list

    # Run a single rclone copy command to download all files in parallel
    rclone copy --files-from="$temp_file_list" "$DRIVER:" "$TARGET_DOWNLOAD" --log-file="$LOG_DOWNLOAD" --progress

    # Clean up the temporary file
    rm "$temp_file_list"

    echo "Download process finished."
}

# Function to extract files
# Function to extract files
extract_files() {
    echo "Starting the extraction process..."

    # Create a temporary file for the list of files to extract
    temp_extract_list=$(mktemp)

    # Loop through all files and check if they need to be added to the temporary list
    for file in $FILES_EXTRACT; do
        
        # Check if the file has an asterisk symbol (*)
        if [[ "$file" == *\** ]]; then
            # Use ls to check the local directory for the file pattern
            result=$(ls "$TARGET_DOWNLOAD" | grep -E "$file")

             # Loop through each result of ls
            while IFS= read -r line; do
                # Construct the full filename relative to $TARGET_DOWNLOAD
                filename="${TARGET_DOWNLOAD}/${line}"

                # Check if the filename is not already in the temp file list
                if ! grep -Fxq "$filename" "$temp_extract_list"; then
                    # Append the filename to the temporary file list
                    echo "$filename" >> "$temp_extract_list"
                fi
            done <<< "$result"
        else
            # If the file does not have an asterisk, directly append it to the temp file list
            adjusted_file="${TARGET_DOWNLOAD}/$file"
            echo "$adjusted_file" >> "$temp_extract_list"
        fi

    done

    # Process the files in parallel using xargs and extract them
    cat "$temp_extract_list" | xargs -I{} -P "$(nproc)" bash -c '
        file="{}"
        base_name=$(basename "$file")
        extract_dir="${EXTRACT_TARGET}/${base_name%.*.*}"
        mkdir -p "$extract_dir"
        echo "Extracting $file to $extract_dir"
        
        # Handle extraction based on file extension
        case "$file" in
            *.tar.gz|*.tgz)
                tar -xzvf "$file" -C "$extract_dir" >> "$EXTRACT_LOG" 2>&1
                ;;
            *.tar.bz2|*.tbz2)
                tar -xjvf "$file" -C "$extract_dir" >> "$EXTRACT_LOG" 2>&1
                ;;
            *.tar)
                tar -xvf "$file" -C "$extract_dir" >> "$EXTRACT_LOG" 2>&1
                ;;
            *)
                echo "Unsupported file type: $file" >> "$EXTRACT_LOG"
                ;;
        esac
    '


    # Clean up the temporary extract list
    rm "$temp_extract_list"

    echo "Extraction process finished."

    # If auto_delete is true, remove the extracted files
    if [ "$AUTO_DELETE" == "true" ]; then
        echo "Auto delete is enabled. Deleting files..."
        rm -f "$TARGET_DOWNLOAD"/*.tar.gz "$TARGET_DOWNLOAD"/*.tar.bz2
    fi
}

mkdir -p $EXTRACT_TARGET $TARGET_DOWNLOAD


# Main logic to process download and extraction
if [ "$DOWNLOAD_ENABLED" == "true" ] && [ -n "$DRIVER" ]; then
    download_files
fi

if [ "$EXTRACT_ENABLED" == "true" ] && [ -n "$EXTRACT_TARGET" ]; then
    extract_files
fi

echo "Finished the process."
