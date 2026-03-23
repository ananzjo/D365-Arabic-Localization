with open("Base Application.ar-JO.xlf", "r", encoding="utf-8") as f:
    lines = f.readlines()
    start = max(0, 278054 - 20)
    end = min(len(lines), 278054 + 20)
    for i in range(start, end):
        print(f"{i+1}: {lines[i]}", end="")
