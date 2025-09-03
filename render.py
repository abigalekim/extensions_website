import csv
import os
import shutil
from pathlib import Path
from jinja2 import FileSystemLoader, Environment

def parse_csv(csv_content):
    """Parse the CSV content and return extensions and compatibility matrix"""
    lines = csv_content.strip().split('\n')
    
    # Parse header (extensions)
    header = lines[0].split(',')
    extensions = [ext.strip() for ext in header[1:]]  # Skip first column header
    
    # Parse compatibility matrix
    matrix = {}
    for i, line in enumerate(lines[1:], 1):
        cells = line.split(',')
        ext_name = cells[0].strip()
        
        if ext_name not in matrix:
            matrix[ext_name] = {}
            
        for j, cell in enumerate(cells[1:]):
            other_ext = extensions[j]
            matrix[ext_name][other_ext] = cell.strip().lower()
    
    return extensions, matrix

def calculate_failure_rate_and_failed_extensions(extension, extensions, matrix):
    """Calculate failure rate and get list of failed extensions"""
    total_tests = 0
    failures = 0
    failed_extensions = set()
    
    # Check row (this extension with others)
    if extension in matrix:
        for other_ext in extensions:
            if other_ext != extension and other_ext in matrix[extension]:
                total_tests += 1
                if matrix[extension][other_ext] == 'no':
                    failures += 1
                    failed_extensions.add(other_ext)
    
    # Check column (others with this extension)
    for other_ext in extensions:
        if other_ext != extension and other_ext in matrix:
            if extension in matrix[other_ext]:
                total_tests += 1
                if matrix[other_ext][extension] == 'no':
                    failures += 1
                    failed_extensions.add(other_ext)
    
    failure_rate = (failures / total_tests * 100) if total_tests > 0 else 0
    return failure_rate, sorted(list(failed_extensions))

def parse_source_code_csv(file_path):
    """Parse source code CSV and return dictionary mapping extension to URL"""
    source_code = {}
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                ext_name = row['Extension Name'].strip()
                source_url = row['Source Code'].strip()
                source_code[ext_name] = source_url
    except FileNotFoundError:
        print(f"Warning: {file_path} not found. Source code links will not be available.")
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
    
    return source_code

def parse_descriptions_csv(file_path):
    """Parse descriptions CSV and return dictionary mapping extension to description"""
    descriptions = {}
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                ext_name = row['Extension Name'].strip()
                description = row['Description'].strip()
                descriptions[ext_name] = description
    except FileNotFoundError:
        print(f"Warning: {file_path} not found. Descriptions will not be available.")
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
    
    return descriptions

def parse_infos_csv(file_path):
    """Parse infos CSV and return dictionary mapping extension to extensibility info"""
    infos = {}
    extensions_list = []
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                ext_name = row['Extension Name'].strip()
                extensions_list.append(ext_name)
                
                # Get extensibility types used
                extensibility_types = []
                if row.get('Functions', '').strip().lower() == 'yes':
                    extensibility_types.append('Functions')
                if row.get('Types', '').strip().lower() == 'yes':
                    extensibility_types.append('Types')
                if row.get('Index Access Methods', '').strip().lower() == 'yes':
                    extensibility_types.append('Index Access Methods')
                if row.get('Storage Managers', '').strip().lower() == 'yes':
                    extensibility_types.append('Storage Managers')
                if row.get('Client Authentication', '').strip().lower() == 'yes':
                    extensibility_types.append('Client Authentication')
                if row.get('Query Processing', '').strip().lower() == 'yes':
                    extensibility_types.append('Query Processing')
                if row.get('Utility Commands', '').strip().lower() == 'yes':
                    extensibility_types.append('Utility Commands')
                
                infos[ext_name] = {
                    'extensibility_types': extensibility_types if extensibility_types else ['None']
                }
    except FileNotFoundError:
        print(f"Warning: {file_path} not found. Extensibility info will not be available.")
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
    
    return infos, extensions_list

def parse_mechanisms_csv(file_path):
    """Parse mechanisms CSV and return dictionary mapping extension to system components"""
    mechanisms = {}
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                ext_name = row['Extension Name'].strip()
                
                # Get system components used
                system_components = []
                if row.get('Memory Allocation', '').strip().lower() == 'yes':
                    system_components.append('Memory Allocation')
                if row.get('Background Workers', '').strip().lower() == 'yes':
                    system_components.append('Background Workers')
                if row.get('Custom Configuration Variables', '').strip().lower() == 'yes':
                    system_components.append('Custom Configuration Variables')
                
                # Check if number of components is 0
                num_components = row.get('Number of Components', '0').strip()
                if num_components == '0' or not system_components:
                    system_components = ['None']
                
                mechanisms[ext_name] = {
                    'system_components': system_components
                }
    except FileNotFoundError:
        print(f"Warning: {file_path} not found. System components info will not be available.")
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
    
    return mechanisms

def get_terminal_outputs(extension, failed_extensions):
    """Get terminal outputs for failed extension pairs"""
    terminal_outputs_by_extension = {}
    
    for failed_ext in failed_extensions:
        # Check both directions: extension_failed and failed_extension
        directions = [
            f"{extension}_{failed_ext}",
            f"{failed_ext}_{extension}"
        ]
        
        for direction in directions:
            terminal_path = os.path.join("total_compat_output", direction, "terminal.txt")
            if os.path.exists(terminal_path):
                try:
                    with open(terminal_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                        # Determine which extension is the "other" one (not the current page's extension)
                        if direction.startswith(f"{extension}_"):
                            other_extension = failed_ext
                            first_ext = extension
                            second_ext = failed_ext
                        else:
                            other_extension = failed_ext
                            first_ext = failed_ext
                            second_ext = extension
                        
                        # Group by the other extension
                        if other_extension not in terminal_outputs_by_extension:
                            terminal_outputs_by_extension[other_extension] = []
                        
                        terminal_outputs_by_extension[other_extension].append({
                            'pair': direction,
                            'first_ext': first_ext,
                            'second_ext': second_ext,
                            'content': content
                        })
                        
                except Exception as e:
                    print(f"Error reading {terminal_path}: {e}")
    
    # Sort the extensions alphabetically and return as a list of tuples
    sorted_outputs = []
    for ext in sorted(terminal_outputs_by_extension.keys()):
        sorted_outputs.append((ext, terminal_outputs_by_extension[ext]))
    
    return sorted_outputs

def generate_website(csv_file_path, build_path="build", include_descriptions=True):
    """Main function to generate the website using Jinja2"""
    
    # Check if layout directory exists
    if not os.path.exists("layout"):
        print("Error: 'layout' directory not found. Please create the layout directory with templates.")
        print("Required files:")
        print("- layout/base.html")
        print("- layout/index.html") 
        print("- layout/results.html")
        print("- layout/extension.html")
        print("- layout/css/custom.css")
        return
    
    # Set up Jinja2 environment
    env = Environment(loader=FileSystemLoader('layout'))
    
    # Read and parse CSV file
    with open(csv_file_path, 'r', encoding='utf-8') as file:
        csv_content = file.read()
    
    # Read additional CSV files
    source_code = parse_source_code_csv("csvs/source_code.csv")
    descriptions = parse_descriptions_csv("csvs/descriptions.csv")
    infos, all_extensions = parse_infos_csv("csvs/infos.csv")
    mechanisms = parse_mechanisms_csv("csvs/mechanisms.csv")
    
    extensions, matrix = parse_csv(csv_content)
    
    # Prepare extension data for results page using all extensions from infos.csv
    extension_data = []
    for extension in all_extensions:
        # Only calculate compatibility if extension exists in compatibility matrix
        if extension in extensions:
            failure_rate, failed_extensions = calculate_failure_rate_and_failed_extensions(extension, extensions, matrix)
            has_compatibility_data = True
        else:
            failure_rate, failed_extensions = 0, []
            has_compatibility_data = False
            
        extension_data.append({
            'name': extension,
            'source_code': source_code.get(extension, ''),
            'description': descriptions.get(extension, 'No description available') if include_descriptions else '',
            'failed_extensions': failed_extensions,
            'has_compatibility_data': has_compatibility_data,
            'include_descriptions': include_descriptions
        })
    
    # Create build directory and copy CSS files
    Path(build_path).mkdir(exist_ok=True)
    Path(os.path.join(build_path, "css")).mkdir(exist_ok=True)
    
    # Copy CSS files specifically
    if os.path.exists("layout/css"):
        shutil.copytree("layout/css", os.path.join(build_path, "css"), dirs_exist_ok=True)
        print("CSS files copied successfully")
    else:
        print("Warning: layout/css directory not found")
    
    # Copy portraits directory if it exists
    if os.path.exists("portraits"):
        shutil.copytree("portraits", os.path.join(build_path, "portraits"), dirs_exist_ok=True)
        print("Portraits directory copied successfully")
    else:
        print("Warning: portraits directory not found")
    
    # Generate index.html
    template = env.get_template('index.html')
    with open(os.path.join(build_path, "index.html"), "w", encoding="utf-8") as f:
        f.write(template.render(page_name='home'))
    
    # Generate results.html
    template = env.get_template('results.html')
    with open(os.path.join(build_path, "results.html"), "w", encoding="utf-8") as f:
        f.write(template.render(extension_data=extension_data, page_name='results', include_descriptions=include_descriptions))
    
    # Generate individual extension pages using all extensions from infos.csv
    template = env.get_template('extension.html')
    for extension in all_extensions:
        # Only calculate compatibility if extension exists in compatibility matrix
        if extension in extensions:
            failure_rate, failed_extensions = calculate_failure_rate_and_failed_extensions(extension, extensions, matrix)
            has_compatibility_data = True
        else:
            failure_rate, failed_extensions = 0, []
            has_compatibility_data = False
        
        # Get terminal outputs for failed extensions
        terminal_outputs = get_terminal_outputs(extension, failed_extensions) if has_compatibility_data else []
        
        with open(os.path.join(build_path, f"{extension}.html"), "w", encoding="utf-8") as f:
            f.write(template.render(
                extension_name=extension,
                failure_rate=failure_rate,
                source_code=source_code.get(extension, ''),
                description=descriptions.get(extension, 'No description available') if include_descriptions else '',
                failed_extensions=failed_extensions,
                terminal_outputs=terminal_outputs,
                extensibility_types=infos.get(extension, {}).get('extensibility_types', ['None']),
                system_components=mechanisms.get(extension, {}).get('system_components', ['None']),
                has_compatibility_data=has_compatibility_data,
                include_descriptions=include_descriptions
            ))
    
    print(f"Website generated successfully in '{build_path}' directory!")
    print(f"Generated {len(all_extensions) + 2} HTML files:")
    print("- index.html (homepage)")
    print("- results.html (results overview)")
    for ext in all_extensions:
        print(f"- {ext}.html")

# Example usage
if __name__ == "__main__":
    # CSV file path updated to match your structure
    csv_file = "csvs/compatibility.csv"
    
    # Set to False to hide descriptions
    show_descriptions = False
    
    # Check if CSV file exists
    if os.path.exists(csv_file):
        generate_website(csv_file, include_descriptions=show_descriptions)
    else:
        print(f"CSV file '{csv_file}' not found. Please ensure the file exists and update the path.")
        print("\nTo use this script:")
        print("1. Save your CSV data to 'csvs/compatibility.csv'")
        print("2. Create layout directory with template files")
        print("3. Run the script: python render.py")
        print("4. Set show_descriptions = False to hide descriptions")