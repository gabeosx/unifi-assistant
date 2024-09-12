import logging
import traceback
import requests
import json
import time

class DataCollector:
    def __init__(self, config):
        self.config = config
        self.session = None
        self.base_url = f"https://{self.config['unifi']['controller_url']}"
        self.site = self.config['unifi'].get('site', 'default')
        logging.debug("DataCollector initialized with config")

    def connect(self):
        logging.debug("Attempting to connect to UniFi Controller")
        try:
            self.session = requests.Session()
            self.session.verify = False  # Disable SSL verification
            login_url = f"{self.base_url}/api/auth/login"
            login_data = {
                "username": self.config['unifi']['username'],
                "password": self.config['unifi']['password']
            }
            response = self.session.post(login_url, json=login_data)
            response.raise_for_status()
            logging.debug("Successfully connected to UniFi Controller")
        except Exception as e:
            logging.error(f"Failed to connect to UniFi Controller: {str(e)}")
            logging.debug(traceback.format_exc())
            raise

    def collect_data(self):
        logging.debug("Starting data collection")
        try:
            self.connect()
            
            logging.debug("Collecting device configuration")
            devices = self.get_devices()
            with open('device_config.json', 'w') as f:
                json.dump(devices, f, indent=2)
            logging.debug("Device configuration collected")

            logging.debug("Collecting performance data")
            performance = self.get_statistics()
            with open('performance_data.json', 'w') as f:
                json.dump(performance, f, indent=2)
            logging.debug("Performance data collected")

            logging.debug("Collecting WiFi scans")
            wifi_scans = self.get_wlan_conf()
            with open('wifi_scans.json', 'w') as f:
                json.dump(wifi_scans, f, indent=2)
            logging.debug("WiFi scans collected")

            logging.debug("Collecting RF environment data")
            rf_data = self.get_rf_environment_data()
            with open('rf_environment.json', 'w') as f:
                json.dump(rf_data, f, indent=2)
            logging.debug("RF environment data collected")

            # Add this to the collect_data method
            client_devices = self.get_client_devices()
            with open('client_devices.json', 'w') as f:
                json.dump(client_devices, f, indent=2)

            # Add this to the collect_data method
            end_time = int(time.time())
            start_time = end_time - (7 * 24 * 60 * 60)  # 7 days ago
            historical_data = self.get_historical_data(start_time, end_time)
            with open('historical_data.json', 'w') as f:
                json.dump(historical_data, f, indent=2)

            # Add this to the collect_data method
            channel_util = self.get_channel_utilization()
            with open('channel_utilization.json', 'w') as f:
                json.dump(channel_util, f, indent=2)

        except Exception as e:
            logging.error(f"Error during data collection: {str(e)}")
            logging.debug(traceback.format_exc())
            raise

    def get_devices(self):
        url = f"{self.base_url}/proxy/network/api/s/{self.site}/stat/device"
        response = self.session.get(url)
        response.raise_for_status()
        return response.json()['data']

    def get_statistics(self):
        url = f"{self.base_url}/proxy/network/api/s/{self.site}/stat/report/daily.site"
        response = self.session.get(url)
        response.raise_for_status()
        return response.json()['data']

    def get_wlan_conf(self):
        url = f"{self.base_url}/proxy/network/api/s/{self.site}/rest/wlanconf"
        response = self.session.get(url)
        response.raise_for_status()
        return response.json()['data']

    def get_rf_environment_data(self):
        logging.debug("Starting RF environment data collection")
        rf_data = {}
        try:
            devices = self.get_devices()
            
            for device in devices:
                if device.get('type') == 'uap':
                    mac = device.get('mac')
                    if mac:
                        logging.debug(f"Collecting RF data for AP {mac}")
                        url = f"{self.base_url}/proxy/network/api/s/{self.site}/stat/spectrum-scan/{mac}"
                        response = self.session.get(url)
                        if response.status_code == 200:
                            rf_data[mac] = response.json()['data']
                            logging.debug(f"RF data collected for AP {mac}")
                        else:
                            logging.warning(f"Failed to retrieve RF data for AP {mac}. Status code: {response.status_code}")
            
            if not rf_data:
                logging.error("Failed to retrieve RF environment data for any access points.")
                raise Exception("No RF data collected")
            
            logging.debug("RF environment data collection completed")
            return rf_data
        except Exception as e:
            logging.error(f"Error collecting RF environment data: {str(e)}")
            logging.debug(traceback.format_exc())
            raise

    def get_client_devices(self):
        url = f"{self.base_url}/proxy/network/api/s/{self.site}/stat/sta"
        response = self.session.get(url)
        response.raise_for_status()
        return response.json()['data']

    def get_historical_data(self, start_time, end_time):
        url = f"{self.base_url}/proxy/network/api/s/{self.site}/stat/report/hourly.site"
        params = {'start': start_time, 'end': end_time}
        response = self.session.get(url, params=params)
        response.raise_for_status()
        return response.json()['data']

    def get_channel_utilization(self):
        url = f"{self.base_url}/proxy/network/api/s/{self.site}/stat/health"
        response = self.session.get(url)
        response.raise_for_status()
        return response.json()['data']
