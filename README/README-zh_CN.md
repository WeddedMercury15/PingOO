# Pingoo
> 释义：这个名字听起来很可爱，而且有点像Goo（胶水）的意思，表示本Ping工具可以把三种协议粘在一起，很灵活，很方便。

＃＃ 入门

为了让您轻松开始使用 GitLab，这里列出了建议的后续步骤。

已经是专业人士了吗？ 只需编辑此 README.md 并使其成为您自己的即可。 想让事情变得简单吗？ [使用底部的模板](#editing-this-readme)！

## 添加你的文件

- [ ] [创建](https://docs.gitlab.com/ee/user/project/repository/web_editor.html#create-a-file) 或 [上传](https://docs.gitlab.com/ ee/user/project/repository/web_editor.html#upload-a-file) 文件
- [ ] [使用命令行添加文件](https://docs.gitlab.com/ee/gitlab-basics/add-file.html#add-a-file-using-the-command-line) 或推送 使用以下命令创建现有的 Git 存储库：

````
cd 现有的_repo
git 远程添加原点 https://gitlab.com/WeddedMercury15/pingoo.git
git分支-M主
git push -uf 起源主要
````

## 与您的工具集成

- [ ] [设置项目集成](https://gitlab.com/WeddedMercury15/pingoo/-/settings/integrations)

## 与您的团队合作

- [ ] [邀请团队成员和协作者](https://docs.gitlab.com/ee/user/project/members/)
- [ ] [创建新的合并请求](https://docs.gitlab.com/ee/user/project/merge_requests/creating_merge_requests.html)
- [ ] [自动关闭合并请求中的问题](https://docs.gitlab.com/ee/user/project/issues/managing_issues.html#looking-issues-automatically)
- [ ] [启用合并请求批准](https://docs.gitlab.com/ee/user/project/merge_requests/approvals/)
- [ ] [设置自动合并](https://docs.gitlab.com/ee/user/project/merge_requests/merge_when_pipeline_succeeds.html)

## 测试和部署

使用 GitLab 中内置的持续集成。

- [ ] [GitLab CI/CD 入门](https://docs.gitlab.com/ee/ci/quick_start/index.html)
- [ ] [使用静态应用程序安全测试 (SAST) 分析代码中的已知漏洞](https://docs.gitlab.com/ee/user/application_security/sast/)
- [ ] [使用 Auto Deploy 部署到 Kubernetes、Amazon EC2 或 Amazon ECS](https://docs.gitlab.com/ee/topics/autodevops/requirements.html)
- [ ] [使用基于拉取的部署来改进 Kubernetes 管理](https://docs.gitlab.com/ee/user/clusters/agent/)
- [ ] [设置受保护环境](https://docs.gitlab.com/ee/ci/environments/protected_environments.html)

***

# 编辑此自述文件

当您准备好自己编写此自述文件时，只需编辑此文件并使用下面方便的模板（或者随意构建您想要的结构 - 这只是一个起点！）。 感谢 [makeareadme.com](https://www.makeareadme.com/) 提供此模板。

## 关于良好自述文件的建议
每个项目都是不同的，因此请考虑以下哪些部分适用于您的项目。 模板中使用的部分是针对大多数开源项目的建议。 另请记住，虽然自述文件可能太长太详细，但太长总比太短好。 如果您认为自述文件太长，请考虑使用另一种形式的文档，而不是删除信息。

＃＃ 姓名
为您的项目选择一个不言自明的名称。

＃＃ 描述
让人们知道您的项目具体可以做什么。 提供上下文并添加指向访问者可能不熟悉的任何参考的链接。 还可以在此处添加功能列表或背景小节。 如果您的项目有其他选择，那么这里是列出差异化因素的好地方。

## 徽章
在某些自述文件中，您可能会看到传达元数据的小图像，例如项目的所有测试是否都通过。 您可以使用 Shields 将一些内容添加到您的自述文件中。 许多服务还提供了添加徽章的说明。

## 视觉效果
根据您正在制作的内容，包含屏幕截图甚至视频可能是个好主意（您经常会看到 GIF 而不是实际视频）。 像 ttygif 这样的工具可以提供帮助，但请查看 Asciinema 以获取更复杂的方法。

＃＃ 安装
在特定的生态系统中，可能有一种常见的安装方式，例如使用 Yarn、NuGet 或 Homebrew。 但是，请考虑阅读您的自述文件的人可能是新手，并且需要更多指导。 列出具体步骤有助于消除歧义并让人们尽快使用您的项目。 如果它仅在特定的上下文中运行，例如特定的编程语言版本或操作系统，或者具有必须手动安装的依赖项，还请添加“要求”小节。

＃＃ 用法
随意使用示例，并尽可能显示预期的输出。 内联您可以演示的最小用法示例会很有帮助，同时如果更复杂的示例太长而无法合理包含在自述文件中，则提供指向更复杂示例的链接。

＃＃ 支持
告诉人们可以去哪里寻求帮助。 它可以是问题跟踪器、聊天室、电子邮件地址等的任意组合。

## 路线图
如果您对将来的版本有想法，最好将它们列在自述文件中。

## 贡献
说明您是否愿意接受捐款以及接受捐款的要求是什么。

对于想要更改项目的人来说，拥有一些有关如何开始的文档会很有帮助。 也许他们应该运行一个脚本或需要设置一些环境变量。 明确这些步骤。 这些说明也可能对未来的您有用。

您还可以记录用于检查代码或运行测试的命令。 这些步骤有助于确保高代码质量并降低更改无意中破坏某些内容的可能性。 如果需要外部设置（例如启动 Selenium 服务器以在浏览器中进行测试），则拥有运行测试的说明尤其有用。

## 作者和致谢
对那些为该项目做出贡献的人表示感谢。

＃＃ 执照
对于开源项目，请说明其如何获得许可。

## 项目状态
如果您的项目已经耗尽精力或时间，请在自述文件顶部添加注释，说明开发已减慢或完全停止。 有人可能会选择分叉您的项目或自愿以维护者或所有者的身份介入，让您的项目继续进行。 您还可以向维护人员提出明确的请求。