import importlib
import os
import textwrap


def load_module(name):
    return importlib.import_module(name)


def build_kernel(triton, tl):
    @triton.jit
    def add_kernel(x_ptr, y_ptr, out_ptr, n_elements, block_size):
        pid = tl.program_id(axis=0)
        offsets = pid * block_size + tl.arange(0, block_size)
        mask = offsets < n_elements
        x = tl.load(x_ptr + offsets, mask=mask)
        y = tl.load(y_ptr + offsets, mask=mask)
        tl.store(out_ptr + offsets, x + y, mask=mask)

    return add_kernel


def main():
    try:
        torch = load_module("torch")
        triton = load_module("triton")
        tl = load_module("triton.language")
    except ModuleNotFoundError:
        print(
            textwrap.dedent(
                """\
                Missing runtime dependencies.
                Install `torch` and `triton`, then rerun.
                On macOS study mode, prefer `TRITON_INTERPRET=1 python vector_add.py`.
                """
            ).strip()
        )
        return

    add_kernel = build_kernel(triton, tl)
    interpret = os.environ.get("TRITON_INTERPRET") == "1"

    if not interpret and not torch.cuda.is_available():
        raise SystemExit("Set TRITON_INTERPRET=1 for study mode on macOS.")

    device = "cpu" if interpret else "cuda"
    x = torch.randn(1024, device=device)
    y = torch.randn(1024, device=device)
    out = torch.empty_like(x)

    kernel = add_kernel[(1,)](x, y, out, x.numel(), block_size=1024)
    asm = getattr(kernel, "asm", {})

    for key in ("ttir", "ttgir", "llir", "ptx"):
        if key in asm:
            print(f"=== {key.upper()} ===")
            print(asm[key])


if __name__ == "__main__":
    main()
