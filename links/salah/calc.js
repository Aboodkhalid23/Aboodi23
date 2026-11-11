// حساب أوقات الصلاة فلكياً لأي مكان بالعالم (نفس معادلات PrayTimes.org المعروفة)
// PT.times(year, month, day, lat, lon, methodKey, asrHanafi) => [فجر، شروق، ظهر، عصر، مغرب، عشاء] بالساعات بتوقيت UTC
(function (root) {
  var R = Math.PI / 180;
  // f: زاوية الفجر، i: زاوية العشاء، im: العشاء بدقايق بعد المغرب، m: زاوية المغرب، o: تعديل دقايق لكل وقت
  var M = {
    MWL: { n: 'رابطة العالم الإسلامي', f: 18, i: 17 },
    EGYPT: { n: 'الهيئة المصرية للمساحة', f: 19.5, i: 17.5 },
    KARACHI: { n: 'جامعة العلوم الإسلامية بكراتشي', f: 18, i: 18 },
    MAKKAH: { n: 'أم القرى (مكة)', f: 18.5, im: 90 },
    ISNA: { n: 'أمريكا الشمالية', f: 15, i: 15 },
    DIYANET: { n: 'رئاسة الشؤون الدينية التركية', f: 18, i: 17, o: [0, -7, 5, 4, 7, 0] },
    JAFARI: { n: 'الجعفري', f: 16, i: 14, m: 4 },
    TEHRAN: { n: 'جامعة طهران', f: 17.7, i: 14, m: 4.5 },
    KUWAIT: { n: 'الكويت', f: 18, i: 17.5 },
    QATAR: { n: 'قطر', f: 18, im: 90 },
    GULF: { n: 'الإمارات والخليج', f: 18.2, i: 18.2 },
    FRANCE: { n: 'مسلمو فرنسا (12 درجة)', f: 12, i: 12 },
    MOROCCO: { n: 'المغرب', f: 19, i: 17 },
    ALGERIA: { n: 'الجزائر', f: 18, i: 17 },
    TUNISIA: { n: 'تونس', f: 18, i: 18 },
    ASIA: { n: 'جنوب شرق آسيا', f: 20, i: 18 },
    RUSSIA: { n: 'روسيا', f: 16, i: 15 },
    // مستخرجة من جدول مسجد توركو: فجر 15 وعشاء 12، وبالصيف الفجر حصة من الليل والعشاء مو أقل من ساعة بعد المغرب
    FINLAND: { n: 'مساجد فنلندا (فجر 15، عشاء 12)', f: 15, i: 12, pf: 0.2365, pi: 0.2, min: 60, o: [0, 0, 0, 0, 2, 0] }
  };
  var BY_COUNTRY = { SA: 'MAKKAH', YE: 'MAKKAH', EG: 'EGYPT', SY: 'EGYPT', LB: 'EGYPT', IQ: 'EGYPT', SD: 'EGYPT', LY: 'EGYPT', PS: 'EGYPT',
    JO: 'KARACHI', PK: 'KARACHI', IN: 'KARACHI', BD: 'KARACHI', AF: 'KARACHI', KW: 'KUWAIT', QA: 'QATAR', AE: 'GULF', OM: 'GULF', BH: 'GULF',
    TR: 'DIYANET', IR: 'TEHRAN', US: 'ISNA', CA: 'ISNA', FR: 'FRANCE', MA: 'MOROCCO', DZ: 'ALGERIA', TN: 'TUNISIA',
    MY: 'ASIA', SG: 'ASIA', ID: 'ASIA', BN: 'ASIA', RU: 'RUSSIA', FI: 'FINLAND' };
  var HANAFI = { PK: 1, IN: 1, BD: 1, AF: 1 };

  function fix(a, b) { a = a - b * Math.floor(a / b); return a < 0 ? a + b : a; }
  function sun(jd) {                                   // ميل الشمس ومعادلة الزمن
    var D = jd - 2451545, g = fix(357.529 + 0.98560028 * D, 360), q = fix(280.459 + 0.98564736 * D, 360);
    var L = fix(q + 1.915 * Math.sin(g * R) + 0.020 * Math.sin(2 * g * R), 360), e = 23.439 - 0.00000036 * D;
    var ra = fix(Math.atan2(Math.cos(e * R) * Math.sin(L * R), Math.cos(L * R)) / R / 15, 24);
    return { d: Math.asin(Math.sin(e * R) * Math.sin(L * R)) / R, eq: q / 15 - ra };
  }
  function times(y, mo, d, lat, lon, key, hanafi) {
    var m = M[key] || M.MWL, jd = Date.UTC(y, mo - 1, d) / 864e5 + 2440587.5 - lon / 360;
    function noon(t) { return fix(12 - sun(jd + t).eq, 24); }
    function at(angle, t, before) {                    // الوقت الي الشمس بيه جوه الأفق بهالزاوية
      var dc = sun(jd + t).d, x = (-Math.sin(angle * R) - Math.sin(dc * R) * Math.sin(lat * R)) / (Math.cos(dc * R) * Math.cos(lat * R));
      var T = Math.acos(x) / R / 15; return noon(t) + (before ? -T : T);
    }
    function asr(t) { var dc = sun(jd + t).d; return at(-Math.atan(1 / ((hanafi ? 2 : 1) + Math.tan(Math.abs(lat - dc) * R))) / R, t); }
    var t = [5, 6, 12, 13, 18, 18].map(function (h) { return h / 24; }), r;
    for (var k = 0; k < 2; k++) {                      // دورتين حتى يثبت الحساب
      r = [at(m.f, t[0], 1), at(0.833, t[1], 1), noon(t[2]), asr(t[3]), m.m ? at(m.m, t[4]) : at(0.833, t[4]), m.im ? NaN : at(m.i, t[5])];
      t = r.map(function (v, i) { return isNaN(v) ? t[i] : v / 24; });
    }
    var rise = r[1], set = at(0.833, t[4]), night = fix(rise - set, 24);
    // المناطق الشمالية: إذا الشفق ما يغيب، نحدد الفجر والعشاء بحصة من الليل حسب الزاوية
    var pf = (m.pf || m.f / 60) * night, pi = (m.pi || (m.i || 18) / 60) * night;
    if (isNaN(r[0]) || fix(rise - r[0], 24) > pf) r[0] = rise - pf;
    if (m.im) r[5] = r[4] + m.im / 60; else if (isNaN(r[5]) || fix(r[5] - set, 24) > pi) r[5] = set + pi;
    if (m.o) r = r.map(function (v, i) { return v + m.o[i] / 60; });
    if (m.min && fix(r[5] - r[4], 24) < m.min / 60) r[5] = r[4] + m.min / 60;
    return r.map(function (v) { return v - lon / 15; }); // من التوقيت الشمسي المحلي إلى UTC
  }
  root.PT = { M: M, times: times, forCountry: function (cc) { return BY_COUNTRY[cc] || 'MWL'; }, hanafi: function (cc) { return !!HANAFI[cc]; } };
})(typeof window !== 'undefined' ? window : module.exports);
