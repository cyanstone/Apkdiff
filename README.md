apkdiff
===

检测两个apk版本的差别
可以显示出文件的增、删、异常等
也可以diff代码的不同（主要是xml文件，因为暂时无法在脚本里反编译得到java源代码）
需要运行在windows平台下，并且需要安装java环境
项目里包含了dex2jar,apktool等工具
输出报告的目录在outReport目录下，生成一个report和一个codediff报告