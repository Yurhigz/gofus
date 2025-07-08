package protocol

type Packet struct {
	Data   []byte
	Length int
}

func ParsePacket(data []byte) *Packet {
	return &Packet{
		Data:   data,
		Length: len(data),
	}
}

func ModifyPacket(packet *Packet) []byte {
	// Logique de modification ici
	return packet.Data
}
