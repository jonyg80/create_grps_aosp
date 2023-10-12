import requests
import xml.etree.ElementTree as ET
import time
import sys

# Set the GitLab API endpoint and access token
api_endpoint = "https://gitlab.com/api/v4"
# get token from cli
access_token = sys.argv[1]

# Set the group ID and path to the Android XML file
aosp1_group_id = "76264102"
xml_file_path = "android.xml"

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
        # print("parent_id", parent_id)
        for group_part in group_parts:
            # time.sleep(1)
            print("group part", group_part)
            # Create the group if it doesn't exist
            # print("parent_id before search", parent_id)
            group_search_url = (
                f"{api_endpoint}/groups/{parent_id}/subgroups?search={group_part}"
            )
            headers = {"Authorization": f"Bearer {access_token}"}
            group_search_response = requests.get(group_search_url, headers=headers)
            # print("group_search_response", group_search_response)
            # print("group_search_response.status_code", group_search_response.status_code)
            # print("group_search_response.json()", group_search_response.json())

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
                url = f"{api_endpoint}/groups"
                headers = {"Authorization": f"Bearer {access_token}"}
                data = {"name": group_part, "path": group_part, "parent_id": parent_id, 'visibility': 'public'}
                response = requests.post(url, headers=headers, data=data)
                if response.status_code == 201:
                    print(f"Group {group_part} created successfully.")
                    parent_id = response.json()["id"]
                    time.sleep(5)
                else:
                    print(f"Error creating group {group_part}: {response.text}")
                    break
