import re
import os
import streamlit as st

# ============================================================
# Functions from Script 1
# ============================================================

def extract_text_between_comma_and_equal(text):
    """Extract text between ',' and '='."""
    text_pattern = r',\s*(.*?)\s*='
    return re.findall(text_pattern, text)

def extract_hex_groups(text):
    """Extract groups of 3 hex values separated by spaces."""
    hex_group_pattern = r'\b([0-9A-Fa-f]{1,2})\s+([0-9A-Fa-f]{1,2})\s+([0-9A-Fa-f]{1,2})\b'
    hex_groups = re.findall(hex_group_pattern, text)
    # Filter out groups where all values are within 4-bit and 8-bit range
    valid_hex_groups = [
        group for group in hex_groups
        if all(int(hex_val, 16) <= 0xFF for hex_val in group)
    ]
    return valid_hex_groups

def zero_pad_hex(hex_value):
    """Zero-pad hex values to 2 digits."""
    return f"{int(hex_value, 16):02X}"

# ============================================================
# Functions from Script 2
# ============================================================

def hex_to_binary(hex_value, bits):
    """Convert hex to binary with a fixed number of bits."""
    return bin(int(hex_value, 16))[2:].zfill(bits)

def binary_not(binary_value):
    """Perform a binary NOT operation."""
    return ''.join('1' if bit == '0' else '0' for bit in binary_value)

def binary_to_hex(binary_value):
    """Convert binary to hex."""
    return hex(int(binary_value, 2))[2:].upper().zfill(2)

def process_24bit_hex(hex_value):
    """Process a 24-bit hex value as per the requirements."""
    # Split into 3 parts (8 bits each)
    hex1, hex2, hex3 = hex_value[:2], hex_value[2:4], hex_value[4:6]

    # Convert each to 8-bit binary
    bin1 = hex_to_binary(hex1, 8)
    bin2 = hex_to_binary(hex2, 8)
    bin3 = hex_to_binary(hex3, 8)

    # Reverse the binary values
    rbin1 = bin1[::-1]
    rbin2 = bin2[::-1]
    rbin3 = bin3[::-1]

    # Perform binary NOT on RBIN3 to get RBIN4
    rbin4 = binary_not(rbin3)

    # Convert reversed binaries back to hex
    ahex1 = binary_to_hex(rbin1)
    ahex2 = binary_to_hex(rbin2)
    ahex3 = binary_to_hex(rbin3)
    ahex4 = binary_to_hex(rbin4)

    # Combine into a 32-bit hex value
    anhex = ahex1 + ahex2 + ahex3 + ahex4

    return anhex

# ============================================================
# New Function to Split 32-bit Hex into Two 16-bit Parts
# ============================================================

def split_32bit_hex_to_16bit(hex_value):
    """Split a 32-bit hex value into two 16-bit parts."""
    if len(hex_value) != 8:
        raise ValueError("Hex value must be 32 bits (8 characters long).")
    part1 = hex_value[:4]  # First 16 bits
    part2 = hex_value[4:]  # Last 16 bits
    return part1, part2

# ============================================================
# Function to Generate XML File
# ============================================================

def generate_xml_file(processed_lines, brand, model):
    """Generate an XML file from processed lines."""
    # Define the base output file name dynamically
    base_output_file = f"{brand}-{model}.irplus"
    output_file = base_output_file

    # Check if the file already exists and add a counter if necessary
    counter = 1
    while os.path.exists(output_file):
        output_file = f"{brand}-{model}_{counter}.irplus"
        counter += 1

    # Prepare the XML content
    xml_content = [
        '<irplus>',
        f'  <device manufacturer="{brand}" model="{model}" columns="12" format="WINLIRC_NEC1" one-pulse="600" one-space="1654" zero-pulse="600" zero-space="522" header-pulse="9051" header-space="4433" gap-space="108161" gap-pulse="601" bits="16" pre-bits="16" rowSplit="3">',
        f'    <button label="{brand}-{model}" labelSize="15.0" span="8" backgroundColor="FF000000"> </button>'
    ]

    # Process all lines
    for line in processed_lines:
        # Split the line into columns, treating the first column as a single entity (even if it contains spaces)
        parts = line.strip().split("\t")  # Split by tab character
        if len(parts) >= 4:  # Ensure the line has exactly 4 columns
            label = parts[0]  # First column (label, may contain spaces)
            hex_value = parts[3]  # Fourth column (two 16-bit values, e.g., "0x20DE 0x50AF")
            button_line = f'    <button label="{label}" labelSize="20.0" span="4">{hex_value}</button>'
            xml_content.append(button_line)
        else:
            st.warning(f"Skipping line due to insufficient columns: {line.strip()}")

    # Finalize the XML content
    xml_content.append("  </device>")
    xml_content.append("</irplus>")

    # Write the XML content to the output file
    with open(output_file, "w") as file:
        file.write("\n".join(xml_content))

    return output_file

# ============================================================
# Streamlit App
# ============================================================

def main():
    st.title("Hexadecimal Processor")
    st.write("Upload a text file containing hexadecimal values for processing.")

    # File uploader
    uploaded_file = st.file_uploader("Upload a file", type=["txt"])

    if uploaded_file is not None:
        # Read the file content
        text = uploaded_file.read().decode("utf-8")

        # Extract text between ',' and '='
        extracted_texts = extract_text_between_comma_and_equal(text)

        # Extract hex groups
        hex_groups = extract_hex_groups(text)

        # Prepare the output for the second script
        output_lines = []
        for i, group in enumerate(hex_groups):
            # Zero-pad each hex value in the group
            padded_group = [zero_pad_hex(hex_val) for hex_val in group]
            # Join the group into a 24-bit hex value
            hex_24bit = ''.join(padded_group)
            # Get the corresponding extracted text (if available)
            extracted_text = extracted_texts[i] if i < len(extracted_texts) else "N/A"
            # Format the output line
            output_line = f"{extracted_text}\t{hex_24bit}"
            # Append to output lines
            output_lines.append(output_line)

        # Process the extracted data using Script 2 logic
        processed_lines = []
        for line in output_lines:
            # Find all 24-bit hex values in the line
            matches = re.findall(r'\b[0-9A-Fa-f]{6}\b', line)
            if matches:
                # Process each 24-bit hex value and append the result after a TAB
                for hex_value in matches:
                    anhex = process_24bit_hex(hex_value)
                    line = line.strip() + '\t' + anhex

                    # Split the 32-bit hex value into two 16-bit parts
                    part1, part2 = split_32bit_hex_to_16bit(anhex)
                    # Prefix with '0x' and separate with a space
                    formatted_parts = f"0x{part1} 0x{part2}"
                    line += f'\t{formatted_parts}\n'
            processed_lines.append(line)

        # Display processed results
        st.subheader("Processed Results")
        for line in processed_lines:
            st.write(line)

        # Input fields for Brand and Model
        st.subheader("Generate XML File")
        brand = st.text_input("Enter Brand", value="Brand")
        model = st.text_input("Enter Model", value="ItemX")

        # Generate XML file
        if st.button("Generate XML File"):
            output_file = generate_xml_file(processed_lines, brand, model)
            st.success(f"File '{output_file}' has been created successfully with Brand='{brand}' and Model='{model}'.")

            # Provide a download link for the generated XML file
            with open(output_file, "r") as file:
                st.download_button(
                    label="Download XML File",
                    data=file,
                    file_name=output_file,
                    mime="text/xml"
                )

# Run the Streamlit app
if __name__ == "__main__":
    main()
