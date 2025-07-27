import yaml

def load_config(config_path):
    with open(config_path, 'r') as file:
        config = yaml.safe_load(file)
    return config

def main():
    config_path = 'config.yaml'
    config = load_config(config_path)
    print("Configuration loaded from", config_path)
    print(yaml.dump(config, default_flow_style=False))

if __name__ == "__main__":
    main()