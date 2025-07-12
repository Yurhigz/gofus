package proxy

import (
	"fmt"
	"net"

	"gofus/internal/proxy/handler"
	"gofus/internal/proxy/logger"
)

type Proxy struct {
	clientAddr string
	serverAddr string
	logger     *logger.Logger
}

func New(clientAddr, serverAddr string) *Proxy {
	return &Proxy{
		clientAddr: clientAddr,
		serverAddr: serverAddr,
		logger:     logger.New("[PROXY] "),
	}
}

func (p *Proxy) Start() error {
	listener, err := net.Listen("tcp", p.clientAddr)
	if err != nil {
		return fmt.Errorf("erreur d'écoute: %v", err)
	}
	defer listener.Close()

	p.logger.Info("Proxy en écoute sur %s", p.clientAddr)

	for {
		clientConn, err := listener.Accept()
		if err != nil {
			p.logger.Error("Erreur d'acceptation de connexion: %v", err)
			continue
		}

		go handler.HandleConnection(clientConn, p.serverAddr, p.logger)
	}
}
