

def solve():
    raw_lines = [line.strip() for line in sys.stdin if line.strip()]
    if not raw_lines:
        return

    first = raw_lines[0].split()
    n, m = int(first[0]), int(first[1])

    # Parse N rows robustly (works whether characters are space-separated or compact)
    grid = []
    if len(raw_lines) >= 1 + n and len(raw_lines[1].split()) == m:
        for i in range(1, 1 + n):
            grid.append(raw_lines[i].split())
    elif len(raw_lines) >= 1 + n and len(raw_lines[1].replace(" ", "")) == m:
        for i in range(1, 1 + n):
            grid.append(list(raw_lines[i].replace(" ", "")))
    else:
        tokens = " ".join(raw_lines[1:]).split()
        idx = 0
        for _ in range(n):
            grid.append(tokens[idx:idx + m])
            idx += m

    # 1. Classify every 'R' cell's rod orientation ('H' or 'V')
    r_orient = [[None] * m for _ in range(n)]
    for r in range(n):
        for c in range(m):
            if grid[r][c] == 'R':
                has_h_r = (c > 0 and grid[r][c - 1] == 'R') or (c + 1 < m and grid[r][c + 1] == 'R')
                has_v_r = (r > 0 and grid[r - 1][c] == 'R') or (r + 1 < n and grid[r + 1][c] == 'R')
                if has_h_r and not has_v_r:
                    r_orient[r][c] = 'H'
                elif has_v_r and not has_h_r:
                    r_orient[r][c] = 'V'
                else:
                    # Isolated 'R' between two 'C's: cable runs along the 'C' axis, rod is perpendicular
                    has_v_c = (r > 0 and grid[r - 1][c] == 'C') and (r + 1 < n and grid[r + 1][c] == 'C')
                    r_orient[r][c] = 'H' if has_v_c else 'V'

    # 2. Group rod segments (including 'C' over-crossings) into unique rod IDs
    rod_id = [[-1] * m for _ in range(n)]
    rod_dir = {}
    next_rod = 0

    # Horizontal rods
    for r in range(n):
        c = 0
        while c < m:
            if grid[r][c] == 'R' and r_orient[r][c] == 'H':
                rid = next_rod
                next_rod += 1
                rod_dir[rid] = 'H'
                while c < m:
                    if grid[r][c] == 'R' and r_orient[r][c] == 'H':
                        rod_id[r][c] = rid
                        c += 1
                    elif (grid[r][c] == 'C' and c + 1 < m
                          and grid[r][c + 1] == 'R' and r_orient[r][c + 1] == 'H'):
                        rod_id[r][c] = rid
                        c += 1
                    else:
                        break
            else:
                c += 1

    # Vertical rods
    for c in range(m):
        r = 0
        while r < n:
            if grid[r][c] == 'R' and r_orient[r][c] == 'V':
                rid = next_rod
                next_rod += 1
                rod_dir[rid] = 'V'
                while r < n:
                    if grid[r][c] == 'R' and r_orient[r][c] == 'V':
                        rod_id[r][c] = rid
                        r += 1
                    elif (grid[r][c] == 'C' and r + 1 < n
                          and grid[r + 1][c] == 'R' and r_orient[r + 1][c] == 'V'):
                        rod_id[r][c] = rid
                        r += 1
                    else:
                        break
            else:
                r += 1

    def valid_moves(r, c, prev):
        moves = []
        # If on an 'R' cell, cable goes straight underneath
        if grid[r][c] == 'R' and prev is not None:
            dr, dc = r - prev[0], c - prev[1]
            nr, nc = r + dr, c + dc
            if 0 <= nr < n and 0 <= nc < m and grid[nr][nc] == 'C':
                moves.append((nr, nc))
            return moves

        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = r + dr, c + dc
            if (nr, nc) == prev:
                continue
            if 0 <= nr < n and 0 <= nc < m:
                if grid[nr][nc] == 'C':
                    # Never move along the axis of a rod we are currently crossing
                    if rod_id[r][c] != -1 and rod_id[r][c] == rod_id[nr][nc]:
                        continue
                    moves.append((nr, nc))
                elif grid[nr][nc] == 'R':
                    rid = rod_id[nr][nc]
                    if rid != -1:
                        if (rod_dir[rid] == 'H' and dr != 0) or (rod_dir[rid] == 'V' and dc != 0):
                            nnr, nnc = nr + dr, nc + dc
                            if 0 <= nnr < n and 0 <= nnc < m and grid[nnr][nnc] == 'C':
                                moves.append((nr, nc))
        return moves

    # 3. Find a cable endpoint on the grid edge (never on a rod)
    start = None
    for r in range(n):
        for c in range(m):
            if (r == 0 or r == n - 1 or c == 0 or c == m - 1) and grid[r][c] == 'C' and rod_id[r][c] == -1:
                if len(valid_moves(r, c, None)) == 1:
                    start = (r, c)
                    break
        if start is not None:
            break

    if start is None:
        print(0)
        return

    # 4. Trace the cable from start to end
    crossings_by_rod = {rid: [] for rid in range(next_rod)}
    curr = start
    prev = None
    visited_states = set()

    while curr is not None:
        state = (curr, prev)
        if state in visited_states:
            break
        visited_states.add(state)

        r, c = curr
        rid = rod_id[r][c]
        if rid != -1:
            crossings_by_rod[rid].append(1 if grid[r][c] == 'C' else -1)

        nxt_list = valid_moves(r, c, prev)
        prev = curr
        curr = nxt_list[0] if nxt_list else None

    # 5. Sum minimum flips across each rod
    total_flips = 0
    for rid, seq in crossings_by_rod.items():
        even_sum = sum(seq[i] for i in range(0, len(seq), 2))
        odd_sum = sum(seq[i] for i in range(1, len(seq), 2))
        total_flips += abs(even_sum - odd_sum) // 2

    print(total_flips)

if __name__ == '__main__':
    solve()
