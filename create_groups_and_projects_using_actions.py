import requests
import xml.etree.ElementTree as ET
import time
import sys

# Set the GitLab API endpoint and access token
api_endpoint = "https://gitgud.io/api/v4"
# get token from cli
access_token = sys.argv[1]

# Set the group ID and path to the Android XML file
aosp1_group_id = "121574"
xml_file_path = "manifest/default.xml"

# Function to check if a project with same name as group exists
def check_project_name_conflict(group_name, parent_id, headers):
    search_url = f"{api_endpoint}/groups/{parent_id}/projects?search={group_name}"
    response = requests.get(search_url, headers=headers, timeout=30)
    
    if response.status_code == 200 and len(response.json()) > 0:
        # Check if any of the projects has the exact same name
        for project in response.json():
            if project["name"].lower() == group_name.lower():
                return project["id"]
    return None

# Function to rename a project
def rename_project(project_id, new_name, headers):
    url = f"{api_endpoint}/projects/{project_id}"
    data = {"name": new_name}
    response = requests.put(url, headers=headers, data=data, timeout=30)
    if response.status_code == 200:
        print(f"Project renamed to {new_name} successfully.")
        return True
    else:
        print(f"Error renaming project: {response.text}")
        return False

# Parse the XML file and extract the project names
tree = ET.parse(xml_file_path)
root = tree.getroot()
for child in root:
    if child.tag == "project":
        # Get the project name and group path
        project_name = child.attrib["name"].split("/")[-1]
        group_path = child.attrib["name"].rpartition("/")[0]
        # print("project_name", project_name)
        print("group_path", group_path)
        # Split the group path into its individual parts
        group_parts = group_path.split("/")
        print("group_parts", group_parts)
        parent_id = aosp1_group_id
        time.sleep(0.5)
        # print("parent_id", parent_id)
        for group_part in group_parts:
            print("group part", group_part)
            # Create the group if it doesn't exist
            # print("parent_id before search", parent_id)
            group_search_url = (
                f"{api_endpoint}/groups/{parent_id}/subgroups?search={group_part}"
            )
            headers = {"Authorization": f"Bearer {access_token}"}
            group_search_response = requests.get(group_search_url, headers=headers)

            # Check if the response is an empty array
            if (
                group_search_response.status_code == 200
                and len(group_search_response.json()) > 0
            ):
                # save group_search_response to file
                # with open("group_search_response_" + group_part + ".json", "w") as f:
                #     f.write(group_search_response.text)
                search_group_id = group_search_response.json()[0]["id"]
                print(f"Group {group_part} found with ID {search_group_id}.")
                parent_id = search_group_id
                # print("parent_id after search", parent_id)
            else:
                print(f"Group path {group_path} is not available.")
                
                # Check if a conflicting project exists with same name as group
                conflicting_project_id = check_project_name_conflict(group_part, parent_id, headers)
                if conflicting_project_id:
                    print(f"Found conflicting project with ID {conflicting_project_id}")
                    new_project_name = f"{group_part}_project"
                    if rename_project(conflicting_project_id, new_project_name, headers):
                        print(f"Renamed conflicting project to {new_project_name}")
                        time.sleep(2)  # Wait for the rename to take effect
                    else:
                        print("Failed to rename conflicting project, skipping group creation")
                        break
                
                url = f"{api_endpoint}/groups"
                headers = {"Authorization": f"Bearer {access_token}"}
                data = {"name": group_part, "path": group_part, "parent_id": parent_id, 'visibility': 'public'}
                response = requests.post(url, headers=headers, data=data)
                if response.status_code == 201:
                    print(f"Group {group_part} created successfully.")
                    parent_id = response.json()["id"]
                    time.sleep(10)
                else:
                    print(f"Error creating group {group_part}: {response.text}")
                    break

        # Create the project in the final subgroup
        # search for project
        # time.sleep(1)
        project_search_url = (
            f"{api_endpoint}/groups/{parent_id}/projects?search={project_name}"
        )
        headers = {"Authorization": f"Bearer {access_token}"}
        project_search_response = requests.get(project_search_url, headers=headers, timeout=30)
        # Check if the response is an empty array
        if (
            project_search_response.status_code == 200
            and len(project_search_response.json()) > 0
        ):
            search_project_id = project_search_response.json()[0]["id"]
            print(f"Project {project_name} found with ID {search_project_id}.")
        else:
            print(f"Project {project_name} is not available.")
            # time.sleep(1)
            url = f'{api_endpoint}/projects'
            headers = {'Authorization': f'Bearer {access_token}'}
            data = {'name': project_name, 'namespace_id': parent_id, 'visibility': 'public'}
            response = requests.post(url, headers=headers, data=data, timeout=30)
            if response.status_code == 201:
                print(f'Project {project_name} created successfully.')
            else:
                print(f'Error creating project {project_name}: {response.text}')
