package main

import "syscall"

// UTF-8 e cores ANSI no console do Windows
func console() {
	k := syscall.NewLazyDLL("kernel32.dll")
	k.NewProc("SetConsoleOutputCP").Call(65001)
	k.NewProc("SetConsoleCP").Call(65001)
	h, err := syscall.GetStdHandle(syscall.STD_OUTPUT_HANDLE)
	if err == nil {
		var modo uint32
		if syscall.GetConsoleMode(h, &modo) == nil {
			k.NewProc("SetConsoleMode").Call(uintptr(h), uintptr(modo|0x0004))
		}
	}
}
