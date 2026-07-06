import numpy as np

def optimize_fertilizer(current_npk, target_npk, prices=None):
    """
    Solves linear programming to find the cheapest combination of Urea, DAP, and MOP
    to satisfy NPK soil deficiencies.
    
    NPK Composition of Standard Fertilizers:
    - Urea: 46% N, 0% P, 0% K
    - DAP:  18% N, 46% P, 0% K
    - MOP:   0% N, 0% P, 60% K
    
    current_npk: list of [N, P, K] current values (ppm or kg/ha equivalent)
    target_npk: list of [N, P, K] target values
    prices: dict of fertilizer prices per kg. Default is:
            {'Urea': 0.6, 'DAP': 0.9, 'MOP': 0.8}
    
    Returns:
    dict containing:
        - 'urea_kg': float (amount of Urea to apply in kg/hectare)
        - 'dap_kg': float (amount of DAP to apply in kg/hectare)
        - 'mop_kg': float (amount of MOP to apply in kg/hectare)
        - 'total_cost': float
        - 'npk_delivered': list [N, P, K]
        - 'status': str ("optimal" or "fallback")
    """
    if prices is None:
        prices = {'Urea': 0.6, 'DAP': 0.9, 'MOP': 0.8}
        
    n_def = max(0.0, target_npk[0] - current_npk[0])
    p_def = max(0.0, target_npk[1] - current_npk[1])
    k_def = max(0.0, target_npk[2] - current_npk[2])
    
    # Try using scipy for linear programming optimization
    try:
        from scipy.optimize import linprog
        
        # Variables: x[0] = Urea, x[1] = DAP, x[2] = MOP
        # Cost coefficient matrix (Objective function: minimize c^T * x)
        c = [prices['Urea'], prices['DAP'], prices['MOP']]
        
        # Inequality constraints: A_ub * x <= b_ub -> we want >=, so we negate
        # N: 0.46 * Urea + 0.18 * DAP >= n_def  -> -0.46 * x0 - 0.18 * x1 <= -n_def
        # P: 0.46 * DAP >= p_def              -> -0.46 * x1 <= -p_def
        # K: 0.60 * MOP >= k_def              -> -0.60 * x2 <= -k_def
        A_ub = [
            [-0.46, -0.18, 0.0],
            [0.0, -0.46, 0.0],
            [0.0, 0.0, -0.60]
        ]
        b_ub = [-n_def, -p_def, -k_def]
        
        # Bounds: quantities must be >= 0
        bounds = [(0, None), (0, None), (0, None)]
        
        res = linprog(c, A_ub=A_ub, b_ub=b_ub, bounds=bounds, method='highs')
        
        if res.success:
            urea_qty = float(res.x[0])
            dap_qty = float(res.x[1])
            mop_qty = float(res.x[2])
            
            n_del = 0.46 * urea_qty + 0.18 * dap_qty
            p_del = 0.46 * dap_qty
            k_del = 0.60 * mop_qty
            
            return {
                'urea_kg': round(urea_qty, 2),
                'dap_kg': round(dap_qty, 2),
                'mop_kg': round(mop_qty, 2),
                'total_cost': round(float(res.fun), 2),
                'npk_delivered': [round(n_del, 2), round(p_del, 2), round(k_del, 2)],
                'status': 'optimal'
            }
    except Exception as e:
        print(f"Scipy optimization failed/unavailable: {e}. Falling back to algebraic solver.")
        
    # Robust Heuristic Fallback (Algebraic direct correction)
    # 1. P is only satisfied by DAP
    dap_qty = p_def / 0.46
    # 2. DAP supplies some N (18%). Remaining N is satisfied by Urea
    n_supplied_by_dap = 0.18 * dap_qty
    n_remaining = max(0.0, n_def - n_supplied_by_dap)
    urea_qty = n_remaining / 0.46
    # 3. K is only satisfied by MOP
    mop_qty = k_def / 0.60
    
    total_cost = urea_qty * prices['Urea'] + dap_qty * prices['DAP'] + mop_qty * prices['MOP']
    n_del = 0.46 * urea_qty + 0.18 * dap_qty
    p_del = 0.46 * dap_qty
    k_del = 0.60 * mop_qty
    
    return {
        'urea_kg': round(dap_qty, 2),
        'dap_kg': round(dap_qty, 2),
        'mop_kg': round(mop_qty, 2),
        'total_cost': round(total_cost, 2),
        'npk_delivered': [round(n_del, 2), round(p_del, 2), round(k_del, 2)],
        'status': 'fallback'
    }

if __name__ == "__main__":
    # Quick debug run
    print(optimize_fertilizer([20, 10, 15], [100, 50, 60]))
