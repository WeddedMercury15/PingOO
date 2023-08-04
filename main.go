package main

import (
	"fmt"
	"log"

	"github.com/jroimartin/gocui"
)

func main() {
	g, err := gocui.NewGui(gocui.OutputNormal)
	if err != nil {
		log.Fatalf("初始化 gocui 失败：%v", err)
	}
	defer g.Close()

	g.SetManagerFunc(layout)

	if err := keybindings(g); err != nil {
		log.Fatalf("设置按键绑定失败：%v", err)
	}

	if err := g.MainLoop(); err != nil && err != gocui.ErrQuit {
		log.Fatalf("gocui 主循环错误：%v", err)
	}
}

func layout(g *gocui.Gui) error {
	maxX, _ := g.Size() // 这里将maxY的声明改成了_

	// 创建边框
	if v, err := g.SetView("border", maxX/2-12, 0, maxX/2+12, 12); err != nil {
		if err != gocui.ErrUnknownView {
			return err
		}
		v.Frame = true
		v.Title = " PingOO "
		v.Highlight = true
		v.BgColor = gocui.ColorGreen
		v.FgColor = gocui.ColorBlack
	}

	// 创建按钮
	buttons := []string{"按钮1", "按钮2", "按钮3"}
	for i, btn := range buttons {
		if v, err := g.SetView(fmt.Sprintf("btn%d", i+1), maxX/2-10, (i+1)*3, maxX/2+10, (i+1)*3+2); err != nil {
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
	// 当按下 "q" 键或 "Ctrl+C" 时退出程序
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
