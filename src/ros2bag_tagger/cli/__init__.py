import typer

from . import batch, convert, tagspec

app = typer.Typer(help="ros2bag tagging utility")

# サブコマンドを登録
app.add_typer(convert.app, name="convert")
app.add_typer(batch.app, name="batch")
app.add_typer(tagspec.app, name="tagspec")
