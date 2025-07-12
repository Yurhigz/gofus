package config

type Config struct {
	ClientAddr string
	ServerAddr string
	BufferSize int
}

func Load() (*Config, error) {
	return &Config{
		ClientAddr: ":8080",
		ServerAddr: "destination.server:80",
		BufferSize: 4096,
	}, nil
}
