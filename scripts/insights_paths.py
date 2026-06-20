"""Ingress-safe relative URL base for Analytics/Environment HTML."""

INSIGHTS_BASE_SCRIPT = """<script>
(function(){
  var p = location.pathname;
  var pages = ['timeline', 'environment', 'story'];
  for (var i = 0; i < pages.length; i++) {
    var needle = '/' + pages[i];
    var idx = p.lastIndexOf(needle);
    if (idx >= 0) {
      var b = document.createElement('base');
      // Direct routes (/timeline) need site root; ingress paths (/foo/timeline) keep prefix.
      b.href = idx === 0 ? '/' : p.slice(0, idx + 1);
      document.head.insertBefore(b, document.head.firstChild);
      return;
    }
  }
  // Event list at / or ingress root — keep relative api/static links under current prefix.
  if (p === '/' || p.endsWith('/')) {
    var b2 = document.createElement('base');
    b2.href = p;
    document.head.insertBefore(b2, document.head.firstChild);
  }
})();
</script>"""
