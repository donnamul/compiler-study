import importlib


def load_symbolic_trace():
    fx = importlib.import_module("torch.fx")
    return fx.symbolic_trace


def f(x, y):
    return x @ y + x


def main():
    try:
        symbolic_trace = load_symbolic_trace()
    except ModuleNotFoundError:
        print("Install `torch` to inspect the FX graph for this experiment.")
        return

    traced = symbolic_trace(f)
    print("=== FX GRAPH ===")
    print(traced.graph)


if __name__ == "__main__":
    main()
