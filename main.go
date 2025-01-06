package main

import (
	"encoding/hex"
	"fmt"
	"log"
)

func main() {
	hexData := "261a240a220a13747970652e616e6b616d612e636f6d2f687a72120b0a0908a3c11c10a30418012a1a280a260a13747970652e616e6b616d612e636f6d2f687a71120f0a0d08a3c11c10082205080a108e12"
	data, err := hex.DecodeString(hexData)
	if err != nil {
		log.Fatal(err)
	}

	fmt.Println("Données décodées:", data)
	fmt.Printf("Données en string : %s\n", string(data))
}
