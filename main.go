package main

import (
	"fmt"
	"log"

	"github.com/jroimartin/gocui"
)

func main() {
	g, err := gocui.NewGui(gocui.OutputNormal)
	if err != nil {
		log.Fatalf("failed to initialize gocui: %v", err)
	}
	defer g.Close()

	g.SetManagerFunc(layout)

	if err := keybindings(g); err != nil {
		log.Fatalf("failed to set keybindings: %v", err)
	}

	if err := g.MainLoop(); err != nil && err != gocui.ErrQuit {
		log.Fatalf("gocui main loop error: %v", err)
	}
}

func layout(g *gocui.Gui) error {
	maxX, maxY := g.Size()

	// Create a new view for the title
	if v, err := g.SetView("title", maxX/2-10, 0, maxX/2+10, 3); err != nil {
		if err != gocui.ErrUnknownView {
			return err
		}
		v.Title = "PingOO"
		v.Wrap = true
	}

	// Create buttons
	buttons := []string{"Button 1", "Button 2", "Button 3"}
	for i, btn := range buttons {
		if v, err := g.SetView(fmt.Sprintf("btn%d", i+1), maxX/2-10, (i+1)*4, maxX/2+10, (i+1)*4+3); err != nil {
			if err != gocui.ErrUnknownView {
				return err
			}
			fmt.Fprintln(v, btn)
			v.Highlight = true
			v.Frame = true
		}
	}

	return nil
}

func keybindings(g *gocui.Gui) error {
	// Quit the application when pressing "q" or "Ctrl+C"
	if err := g.SetKeybinding("", gocui.KeyCtrlC, gocui.ModNone, quit); err != nil {
		return err
	}
	if err := g.SetKeybinding("", 'q', gocui.ModNone, quit); err != nil {
		return err
	}

	return nil
}

func quit(g *gocui.Gui, v *gocui.View) error {
	return gocui.ErrQuit
}
