package main

import (
	"fmt"
	"os"

	ui "github.com/gizak/termui/v3"
	"github.com/gizak/termui/v3/widgets"
)

func main() {
	if err := ui.Init(); err != nil {
		fmt.Printf("failed to initialize termui: %v", err)
		os.Exit(1)
	}
	defer ui.Close()

	// 创建一个全屏的布局
	grid := ui.NewGrid()
	grid.SetRect(0, 0, 100, 40)

	// 创建一个标题
	title := widgets.NewParagraph()
	title.Text = "PingOO"
	title.SetRect(0, 0, 100, 5)
	title.TextStyle.Fg = ui.ColorYellow
	title.Border = false
	title.TextStyle.Modifier = ui.ModifierBold

	// 创建三个按钮
	btn1 := widgets.NewButton("Button 1")
	btn1.SetRect(25, 10, 45, 13)
	btn1.TextStyle.Fg = ui.ColorWhite
	btn1.BorderStyle.Fg = ui.ColorCyan

	btn2 := widgets.NewButton("Button 2")
	btn2.SetRect(25, 15, 45, 18)
	btn2.TextStyle.Fg = ui.ColorWhite
	btn2.BorderStyle.Fg = ui.ColorCyan

	btn3 := widgets.NewButton("Button 3")
	btn3.SetRect(25, 20, 45, 23)
	btn3.TextStyle.Fg = ui.ColorWhite
	btn3.BorderStyle.Fg = ui.ColorCyan

	// 添加组件到布局
	grid.Set(
		ui.NewRow(1.0/6, title),
		ui.NewRow(1.0/6, widgets.NewSpacer()),
		ui.NewRow(1.0/6, btn1),
		ui.NewRow(1.0/6, widgets.NewSpacer()),
		ui.NewRow(1.0/6, btn2),
		ui.NewRow(1.0/6, widgets.NewSpacer()),
		ui.NewRow(1.0/6, btn3),
	)

	ui.Render(grid)

	// 监听终端输入
	uiEvents := ui.PollEvents()
	for {
		e := <-uiEvents
		if e.Type == ui.KeyboardEvent && e.ID == "q" {
			break
		}
	}
}
