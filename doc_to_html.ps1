# This script extracts the user documentation from README.md and converts it to HTML format in README.html

# With Powershell 6, we could do :
#$md = ConvertFrom-Markdown -Path .\README.md
#$md.Html | Out-File -Encoding utf8 .\README.html
# (note that this would extract the technical documentation as well)

# Without Powershell 6, we extract by hand :

# Read the file
$readme = Get-Content ./README.md -Encoding ASCII
# Extract only the user manual
$oneString = if ($readme -join "`n" -match '(## User manual[\s\S]*)[^#]##[^#]') { $matches[1] }

# Convert to HTML
$regexps = @(
    @("## User manual", '## Image2Touch user manual'),
    @("### (.*)", '<h2>$1</h2>'),
    @("## (.*)", '<h1>$1</h1>'),
    @("(?<=\n)(\s*-.+\n)+", "<ul>`n`$0</ul>`n"),
    @("(?<=\n)\s*-(.+)\n", "<li>`$1</li>`n"),
    @("\[([^\]]+)\]\(([^\)]+)\)",'<a href=$2>$1</a>'),
    @("(?<=[\w.])\n\n(?=\w)",'<br/>')
)

$res = $oneString
$regexps |ForEach-Object {
    $res = $res -creplace $_[0],$_[1]
}

# Add root HTML tags and write to the output file
Set-Content -Path ./help.html -Value @("<html>", "<body>", "", $res, "</body>", "</html>") -Encoding ASCII