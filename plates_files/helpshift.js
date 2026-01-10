(function () {
  const PLATFORM_ID = 'scopely_platform_20200804212606506-b27e89d8bb06581',
    DOMAIN = 'scopely',
    LANGUAGE = 'en';
  window.helpshiftConfig = {
    platformId: PLATFORM_ID,
    domain: DOMAIN,
    language: LANGUAGE,
  };
})();
// eslint-disable-next-line
!(function (t, e) {
  if ('function' != typeof window.Helpshift) {
    let n = function () {
      n.q.push(arguments);
    };
    n.q = [];
    window.Helpshift = n;
    let i,
      a = t.getElementsByTagName('script')[0];
    if (t.getElementById(e)) return;
    i = t.createElement('script');
    i.async = !0;
    i.id = e;
    i.src = 'https://webchat.helpshift.com/webChat.js';
    let o = function () {
      window.Helpshift('init');
    };
    window.attachEvent
      ? i.attachEvent('onload', o)
      : i.addEventListener('load', o, !1);
    a.parentNode.insertBefore(i, a);
  } else window.Helpshift('update');
})(document, 'hs-chat');
