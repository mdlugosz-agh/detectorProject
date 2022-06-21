import requests
import yaml

server_url = "http://localhost:5000"

def main():
    with open('resources/cameras.yml', 'r') as ymlfile:
        cameras_data = yaml.load(ymlfile, Loader=yaml.FullLoader)
    
    # Read avaible camera
    res = requests.get(server_url + "/cameras/get")
    cameras_active = res.json();

    for camera_name, camera_data in cameras_data.items() :
        # Add or update camera data

        if str(camera_data['index']) in cameras_active:
            # Update
            res = requests.get(server_url + "/cameras/update", params=camera_data)
            print("Update camera:{}, result:{}".format(camera_name, res.text))
        else:
            # Add
            res = requests.get(server_url + "/cameras/create", params=camera_data)
            print("Add camera:{}, result:{}".format(camera_name, res.text))

            # Activate camera
            res = requests.get(server_url + "/cameras/activate", 
                params={'index' : camera_data['index'], 'active' : 'true'})
            print("Activate camera:{}".format(res.text));

if __name__ == "__main__":
    main()