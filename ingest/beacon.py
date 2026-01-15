HV_BEACON_SCRIPT = """
(timeout = 5000) => {
    return new Promise((resolve) => {
        let resolved = false;
        
        const finish = (reason) => {
            if (resolved) return;
            resolved = true;
            resolve(reason);
        };
        
        // Failsafe timeout
        setTimeout(() => finish("timeout"), timeout);
        
        // 1. Check for requestIdleCallback (Standard)
        if ('requestIdleCallback' in window) {
            requestIdleCallback(() => finish("idle_callback"));
            return;
        }
        
        // 2. Check for Angular
        if (window.getAllAngularTestabilities) {
             Promise.all(
                window.getAllAngularTestabilities().map(t => t.whenStable())
             ).then(() => finish("angular_stable"));
             return;
        }
        
        // 3. Fallback: simple timeout if nothing else
        setTimeout(() => finish("fallback_timer"), 500);
    });
}
"""
