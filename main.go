package main

import (
    "log"
    
    "gofus/internal/proxy"
    "gofus/config"
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
