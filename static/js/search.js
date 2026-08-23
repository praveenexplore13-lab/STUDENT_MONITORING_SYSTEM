// ==========================================
// GLOBAL SEARCH
// ==========================================

document.addEventListener('DOMContentLoaded', function() {
    const searchInput = document.getElementById('globalSearch');
    const searchResults = document.getElementById('searchResults');
    
    if (!searchInput) return;
    
    let timeoutId = null;
    
    searchInput.addEventListener('input', function() {
        const query = this.value.trim();
        
        clearTimeout(timeoutId);
        
        if (query.length < 2) {
            searchResults.style.display = 'none';
            return;
        }
        
        timeoutId = setTimeout(function() {
            fetch(`/search/api?q=${encodeURIComponent(query)}`)
                .then(response => response.json())
                .then(data => {
                    if (data.results && data.results.length > 0) {
                        showResults(data.results);
                    } else {
                        showNoResults(query);
                    }
                })
                .catch(error => {
                    console.error('Search error:', error);
                });
        }, 300);
    });
    
    function showResults(results) {
        let html = '<ul style="list-style:none;padding:0;margin:0;">';
        results.forEach(result => {
            html += `
                <li style="padding:10px 15px;border-bottom:1px solid #e2e8f0;display:flex;justify-content:space-between;align-items:center;">
                    <div>
                        <span style="font-weight:600;">${result.name}</span>
                        <span style="color:#64748b;font-size:13px;margin-left:10px;">${result.roll_number}</span>
                        <span style="color:#94a3b8;font-size:12px;display:block;">${result.department}</span>
                    </div>
                    <a href="/admin/student/${result.id}" style="color:#6366f1;text-decoration:none;font-size:13px;">View</a>
                </li>
            `;
        });
        html += '</ul>';
        searchResults.innerHTML = html;
        searchResults.style.display = 'block';
    }
    
    function showNoResults(query) {
        searchResults.innerHTML = `
            <div style="padding:20px;text-align:center;color:#94a3b8;">
                <i class="fas fa-search"></i> No results for "${query}"
            </div>
        `;
        searchResults.style.display = 'block';
    }
    
    document.addEventListener('click', function(e) {
        if (!searchInput.contains(e.target) && !searchResults.contains(e.target)) {
            searchResults.style.display = 'none';
        }
    });
});