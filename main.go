package main

import (
	"gofus/config"
	"gofus/internal/proxy"
	"log"
)

func main() {
	cfg, err := config.Load()
	if err != nil {
		log.Fatalf("Erreur de configuration: %v", err)
	}

	proxy := proxy.New(cfg.ClientAddr, cfg.ServerAddr)
	if err := proxy.Start(); err != nil {
		log.Fatalf("Erreur du proxy: %v", err)
	}

}
