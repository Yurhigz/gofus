package network

import (
	"io"
	"net"
)

func Dial(network, address string) (net.Conn, error) {
	return net.Dial(network, address)
}

func Read(conn net.Conn, buffer []byte) ([]byte, error) {
	n, err := conn.Read(buffer)
	if err != nil {
		if err == io.EOF {
			return buffer[:n], nil
		}
		return nil, err
	}
	return buffer[:n], nil
}

func Write(conn net.Conn, data []byte) error {
	_, err := conn.Write(data)
	return err
}
