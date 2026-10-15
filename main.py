import base64
import io

import numpy as np
from flask import Flask, render_template_string, request
from matplotlib.figure import Figure

app = Flask(__name__)

PAGINA = """
<!doctype html>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Plotador de funções</title>
<style>
  body { font-family: sans-serif; max-width: 800px; margin: 2rem auto; padding: 0 1rem; }
  input, button { font-size: 1rem; padding: .4rem; }
  img { width: 100%; }
  .erro { color: #c00; }
</style>

<h1>Plotador de funções</h1>
<form>
  y = <input name="f" value="{{ texto }}" size="28">
  x de <input name="xmin" value="{{ xmin }}" size="4">
  até <input name="xmax" value="{{ xmax }}" size="4">
  <button>Plotar</button>
</form>

{% if erro %}<p class="erro">{{ erro }}</p>{% endif %}
{% if imagem %}<img src="data:image/png;base64,{{ imagem }}">{% endif %}

"""

# Nomes que podem aparecer na função digitada
NOMES = {
    "sen": np.sin, "sin": np.sin, "cos": np.cos, "tan": np.tan,
    "raiz": np.sqrt, "sqrt": np.sqrt, "ln": np.log, "log": np.log10,
    "exp": np.exp, "abs": np.abs, "pi": np.pi, "e": np.e,
}


@app.route("/")
def index():
    texto = request.args.get("f", "sen(x)")
    xmin = request.args.get("xmin", "-10")
    xmax = request.args.get("xmax", "10")
    imagem = erro = None

    try:
        x = np.linspace(float(xmin), float(xmax), 1000)
        with np.errstate(all="ignore"):
            y = eval(texto.replace("^", "**"), {"__builtins__": {}}, {**NOMES, "x": x})
        y = np.broadcast_to(np.asarray(y, dtype=float), x.shape).copy()

        # Ajusta a altura do gráfico e quebra a linha em assíntotas (ex.: 1/x)
        y[np.abs(y) > 1e6] = np.nan
        lo, hi = np.nanpercentile(y, [2, 98])
        altura = max(hi - lo, 1e-9)
        y[:-1][np.abs(np.diff(y)) > 3 * altura] = np.nan

        fig = Figure(figsize=(8, 5))
        ax = fig.subplots()
        ax.plot(x, y, linewidth=2)
        ax.set_ylim(lo - altura * 0.15, hi + altura * 0.15)
        ax.axhline(0, color="black", linewidth=1)
        ax.axvline(0, color="black", linewidth=1)
        ax.grid(True, alpha=0.4)

        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=110, bbox_inches="tight")
        imagem = base64.b64encode(buf.getvalue()).decode()
    except Exception:
        erro = "Não consegui entender essa função. Confira a digitação e os valores de x."

    return render_template_string(PAGINA, texto=texto, xmin=xmin, xmax=xmax,
                                  imagem=imagem, erro=erro)


if __name__ == "__main__":
    app.run(debug=True)
