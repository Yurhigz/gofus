package handler

import (
	"net"

    "gofus/internal/proxy/logger"
    "gofus/internal/proxy/protocol"
    "gofus/pkg/network"
)

func HandleConnection(clientConn net.Conn, serverAddr string, logger *logger.Logger) {
	defer clientConn.Close()

	serverConn, err := network.Dial("tcp", serverAddr)
	if err != nil {
		logger.Error("Erreur de connexion au serveur: %v", err)
		return
	}
	defer serverConn.Close()

	go processTraffic(clientConn, serverConn, "CLIENT -> SERVEUR", logger)
	go processTraffic(serverConn, clientConn, "SERVEUR -> CLIENT", logger)
}

func processTraffic(src, dst net.Conn, direction string, logger *logger.Logger) {
	buffer := make([]byte, 4096)
	for {
		data, err := network.Read(src, buffer)
		if err != nil {
			logger.Error("Erreur de lecture %s: %v", direction, err)
			return
		}

		packet := protocol.ParsePacket(data)
		logger.Info("%s - Paquet analysé: %v", direction, packet)

		modifiedData := protocol.ModifyPacket(packet)

		if err := network.Write(dst, modifiedData); err != nil {
			logger.Error("Erreur d'écriture %s: %v", direction, err)
			return
		}
	}
}
