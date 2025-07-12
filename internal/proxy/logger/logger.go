package logger

import (
	"log"
)

type Logger struct {
	*log.Logger
}

func New(prefix string) *Logger {
	return &Logger{
		Logger: log.New(log.Writer(), prefix, log.LstdFlags),
	}
}

func (l *Logger) Info(format string, v ...interface{}) {
	l.Printf("INFO: "+format, v...)
}

func (l *Logger) Error(format string, v ...interface{}) {
	l.Printf("ERROR: "+format, v...)
}
