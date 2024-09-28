import os
import time
import logging
import traceback
from autogen import AssistantAgent, UserProxyAgent, GroupChat, GroupChatManager
import yaml
import urllib3
import json

import requests
from urllib3.exceptions import InsecureRequestWarning
import ssl
from data_collector import DataCollector  # Add this import

# Add this at the beginning of your script to suppress InsecureRequestWarning
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

def load_config():
    with open('config.yaml', 'r') as config_file:
        return yaml.safe_load(config_file)

with open('config.yaml', 'r') as config_file:
    config = yaml.safe_load(config_file)

def create_agents():
    ai_provider_config = {
        "model": config['ai_provider']['model'],
        "api_key": config['ai_provider']['api_key'],
        "api_type": config['ai_provider']['api_type']
    }

    user_proxy = UserProxyAgent(
        name="Human",
        system_message="A human user interacting with AI agents to analyze WiFi network data.",
        human_input_mode="NEVER",  # Change this from "ALWAYS" to "NEVER"
        max_consecutive_auto_reply=0,
        code_execution_config={
            "work_dir": "coding",
            "use_docker": False
        }
    )

    network_analyst = AssistantAgent(
        name="NetworkAnalyst",
        system_message="You analyze network data and provide recommendations based on the given prompt.",
        llm_config=ai_provider_config
    )

    return user_proxy, network_analyst

def run_group_chat():
    config = load_config()
    data_collector = DataCollector(config)
    
    try:
        logging.info("Starting data collection")
        data_collector.collect_data()
        logging.info("Data collection completed successfully")
    except Exception as e:
        logging.error(f"Error during data collection: {str(e)}")
        return f"Data collection failed: {str(e)}"

    logging.info("Creating agents")
    user_proxy, network_analyst = create_agents()
    logging.info("Agents created successfully")

    logging.info("Generating static prompt")
    static_prompt = """
    You are a network optimization expert specializing in UniFi networks. Analyze the following datasets to provide specific recommendations for optimizing WiFi performance. Your recommendations should aim to improve coverage, reduce interference, and enhance client connectivity and throughput. However, be mindful to avoid any new problems, such as overlapping channels or suboptimal configurations. Ensure that each recommendation considers potential side effects and mitigates them.

    Datasets:
    1. RF Environment Data (rf_environment.json): This dataset includes information about the radio frequency environment, such as:
    - Channels
    - Interference levels
    - Channel utilization
    - Channel width

    2. WiFi Scans (wifi_scans.json): This dataset provides WiFi configuration details, including:
    - Enabled WLAN bands (wlan_band)
    - DTIM intervals for various bands (dtim_ng, dtim_na, dtim_6e)
    - Minimum data rates (minrate_na_data_rate_kbps, minrate_ng_data_rate_kbps)
    - Band steering settings and security configurations

    3. Device Configuration (device_config.json): This dataset provides details on device configurations, such as:
    - AP group configurations (ap_group_ids)
    - Network configurations (networkconf_id)
    - Rate setting preferences (minrate_setting_preference)

    4. Performance Data (performance_data.json): This dataset includes performance metrics for various sites, such as:
    - Latency (latency)
    - Throughput (throughput)
    - Overall site performance metrics

    5. Client Data (client_devices.json): This dataset provides details on client devices, such as:
    - Signal strength (rssi)
    - Noise level (noise)
    - Transmit rate (tx_rate)
    - Receive rate (rx_rate)
    - Tx retries (tx_retries)
    - Rx retries (rx_retries)
    - Tx retry percentage (wifi_tx_retries_percentage)

    The analysis you will perform must adhere to the following requirements:
    - Channel Selection and Interference Mitigation: Analyze the RF Environment Data to identify channels with the least interference and utilization. Recommend a channel a channel width for each band on each access point to minimize overlap and interference while ensuring coverage.
    - Prevent Overlapping Channels or New Issues: Ensure that all recommended changes do not introduce new problems, such as overlapping channels (e.g. recommending the same channel on multiple access points), excessive power levels causing interference, or settings that may impact specific types of devices negatively (e.g., disabling 2.4 GHz for IoT devices).
    
    I will now provide you with the data files in separate messages. After receiving all the data, please provide your analysis and recommendations.
    """
    logging.info("Static prompt generated")

    # Send the initial prompt
    response = user_proxy.initiate_chat(network_analyst, message=static_prompt)
    print("\nInitial response:")
    print(response)

    # Send data files in separate messages
    data_files = ['device_config.json', 'performance_data.json', 'wifi_scans.json', 'rf_environment.json', 'client_devices.json']
    for file in data_files:
        with open(file, 'r') as f:
            data = json.load(f)
        data_message = f"Here is the content of {file}:\n{json.dumps(data, separators=(',', ':'))}"
        response = user_proxy.send(data_message, network_analyst)
        print(f"\nResponse after sending {file}:")
        print(response)

    # Request analysis
    # analysis_request = "Now that you have all the data, please provide your analysis and recommendations based on the requirements outlined in the initial prompt."
    
    # logging.info("Generating final analysis")
    # try:
    #     analysis_response = user_proxy.send(analysis_request, network_analyst)
    #     # logging.info(f"Final analysis generated successfully. Response length: {len(analysis_response)}")
    #     if not analysis_response.strip():
    #         logging.warning("Final analysis response is empty")
    #     logging.debug(f"Raw response: {analysis_response}")
    # except Exception as e:
    #     logging.error(f"Error generating final analysis: {str(e)}")
    #     logging.debug(f"Error details: {traceback.format_exc()}")
    #     return f"Final analysis failed: {str(e)}"

    # print("\nFinal analysis:")
    # print(analysis_response)

    # return "Analysis completed."

    # Allow user to ask follow-up questions
    while True:
        follow_up_question = input("\nAsk a follow-up question (type 'exit' to quit): ")
        if follow_up_question.lower() == "exit":
            break
        response = user_proxy.send(follow_up_question, network_analyst)
        print(f"\nResponse to follow-up question: {response}")

    return "Analysis completed."



# Main execution
if __name__ == "__main__":
    try:
        analysis_result = run_group_chat()
        print("\nAnalysis result:")
        print(analysis_result)
    except Exception as e:
        logging.error(f"An error occurred during execution: {str(e)}")
        logging.debug(f"Error details: {traceback.format_exc()}")



