export interface ResourceOption {
  label: string;
  value: string;
}

export interface Resources {
  api_keys: ResourceOption[];
  teams: ResourceOption[];
  models: ResourceOption[];
}
