# Gera PDF + EPUB da amostra traduzida (Prólogo + início do Cap. I) para cada idioma.
import html, json, os, subprocess, uuid, zipfile, datetime, io
from PIL import Image
E = html.escape
L = {
 'en': dict(name='English', dir='ltr', font='"Bitstream Charter",Charter,Georgia,serif', series='Between the Web and the Hook series', sample='free sample',
    end_t='End of the sample', end=['You have read the Prologue and the opening of Chapter I of <i>Wallace Ross</i>, translated from the original Portuguese.', 'The complete book is available in Portuguese on Amazon.', 'If you liked it, pass it on. This is how this story travels: from hand to hand, like a dandelion seed.'],
    lic='© 2026 Ailig Qarchi. Free sample: it may be shared freely, unchanged and free of charge. Translation produced with the help of artificial intelligence.'),
 'es': dict(name='Español', dir='ltr', font='"Bitstream Charter",Charter,Georgia,serif', series='Serie Entre la Telaraña y el Anzuelo', sample='muestra gratuita',
    end_t='Fin de la muestra', end=['Has leído el Prólogo y el comienzo del Capítulo I de <i>Wallace Ross</i>, traducidos del original en portugués.', 'El libro completo está disponible en portugués en Amazon.', 'Si te gustó, pásalo. Así viaja esta historia: de mano en mano, como semilla de diente de león.'],
    lic='© 2026 Ailig Qarchi. Muestra gratuita: puede compartirse libremente, sin cambios y sin cobrar. Traducción realizada con ayuda de inteligencia artificial.'),
 'zh': dict(name='中文', dir='ltr', font='"Noto Serif CJK SC","Noto Sans CJK SC",serif', series='“蛛网与鱼钩之间”系列', sample='免费试读',
    end_t='试读结束', end=['你读完了《华莱士·罗斯》的序章和第一章开头，译自葡萄牙语原著。', '完整版图书目前以葡萄牙语在亚马逊发售。', '如果你喜欢，请把它传下去。这个故事就是这样旅行的：从一只手到另一只手，像一颗蒲公英的种子。'],
    lic='© 2026 Ailig Qarchi。免费试读：可自由分享，但不得修改，不得收费。译文借助人工智能完成。', title='华莱士·罗斯'),
 'hi': dict(name='हिन्दी', dir='ltr', font='"Noto Serif Devanagari","Noto Sans Devanagari",serif', series='जाल और काँटे के बीच शृंखला', sample='निःशुल्क अंश',
    end_t='अंश समाप्त', end=['आपने <i>वालेस रॉस</i> की प्रस्तावना और अध्याय I की शुरुआत पढ़ी, जो मूल पुर्तगाली से अनूदित है।', 'पूरी किताब पुर्तगाली में Amazon पर उपलब्ध है।', 'अगर आपको पसंद आई, तो इसे आगे बढ़ाइए। यह कहानी ऐसे ही यात्रा करती है: एक हाथ से दूसरे हाथ, सिंहपर्णी के बीज की तरह।'],
    lic='© 2026 Ailig Qarchi। निःशुल्क अंश: बिना बदलाव और बिना शुल्क के स्वतंत्र रूप से साझा किया जा सकता है। अनुवाद कृत्रिम बुद्धिमत्ता की सहायता से किया गया।', title='वालेस रॉस'),
 'ar': dict(name='العربية', dir='rtl', font='"Noto Naskh Arabic","Noto Sans Arabic",serif', series='سلسلة بين الشبكة والصنّارة', sample='عيّنة مجانية',
    end_t='نهاية العيّنة', end=['قرأتَ التمهيد وبداية الفصل الأول من <i>والاس روس</i>، مترجَمين عن الأصل البرتغالي.', 'الكتاب الكامل متوفّر بالبرتغالية على أمازون.', 'إن أعجبك، فمرّره إلى غيرك. هكذا تسافر هذه القصة: من يد إلى يد، كبذرة الهندباء.'],
    lic='© 2026 Ailig Qarchi. عيّنة مجانية: يجوز تداولها بحرّية، دون تعديل ودون مقابل. أُنجزت الترجمة بمساعدة الذكاء الاصطناعي.', title='والاس روس'),
}
COVER = '/mnt/project-files/serie/pipeline_pdf/final_registro/cover.jpg'
def parse(fn):
    out = []
    for blk in open(fn, encoding='utf-8').read().strip().split('\n## '):
        lines = blk.strip().lstrip('# ').split('\n')
        n, t = [x.strip() for x in lines[0].split('|')]
        out.append((n, t, [l.strip() for l in lines[1:]]))
    return out
def body(chs):
    h = ''
    for n, t, ps in chs:
        h += f'<section class="chap">' + (f'<div class="cnum">{E(n)}</div>' if n else '') + f'<h2>{E(t)}</h2><div class="orn">✦</div>'
        first = True
        for p in ps:
            if p == '*': h += '<div class="sep">✦</div>'; first = True; continue
            h += f'<p class="{"first" if first else ""}">{E(p)}</p>'; first = False
        h += '</section>'
    return h
for code, m in L.items():
    chs = parse(f'{code}.txt'); title = m.get('title', 'Wallace Ross'); d = m['dir']
    endsec = f'<section class="chap end"><h2>{E(m["end_t"])}</h2><div class="orn">✦</div>' + ''.join(f'<p class="first c">{x}</p>' for x in m['end']) + '<p class="first c site">ailigqarchi.com.br</p>' + f'<p class="first c lic">{E(m["lic"])}</p></section>'
    css = f'''@page{{size:140mm 210mm;margin:18mm 16mm 20mm}}body{{font-family:{m["font"]};font-size:10.5pt;line-height:1.6;color:#1d1d1d}}
section{{page-break-before:always}}.cover{{page:cover;margin:0}}@page cover{{margin:0}}.cover img{{width:140mm;height:210mm;object-fit:cover;display:block}}
.title{{text-align:center;padding-top:45mm}}.title h1{{font-size:24pt;font-weight:normal;margin:4mm 0}}.series{{font-size:9pt;letter-spacing:.12em;color:#555}}.author{{margin-top:12mm;font-size:12pt;letter-spacing:.1em}}
.cnum{{text-align:center;font-size:9pt;letter-spacing:.2em;color:#555;margin-top:18mm;text-transform:uppercase}}h2{{text-align:center;font-weight:normal;font-style:italic;font-size:17pt;margin:3mm 0 1mm}}
.orn,.sep{{text-align:center;color:#666;margin:2mm 0 7mm}}p{{margin:0;text-align:justify;text-indent:1.3em}}p.first{{text-indent:0}}p.c{{text-align:center;margin-bottom:4mm}}.site{{margin-top:10mm;letter-spacing:.15em;font-size:9pt}}.lic{{font-size:8pt;color:#666;margin-top:8mm}}.end{{padding-top:25mm}}'''
    doc = f'<!doctype html><html lang="{code}" dir="{d}"><head><meta charset="utf-8"><title>{E(title)}</title><style>{css}</style></head><body><div class="cover"><img src="file://{COVER}"></div><section class="title"><div class="series">{E(m["series"])}</div><h1>{E(title)}</h1><div class="orn">✦</div><div class="author">Ailig Qarchi</div><p class="first c lic" style="margin-top:40mm">{E(m["lic"])}</p></section>{body(chs)}{endsec}</body></html>'
    open(f'{code}.html', 'w', encoding='utf-8').write(doc)
    subprocess.run(['node', 'pdf.js', os.path.abspath(f'{code}.html'), os.path.abspath(f'Wallace_Ross_amostra_{code}.pdf')], check=True)
    # EPUB
    im = Image.open(COVER).convert('RGB'); im = im.resize((1000, int(im.height * 1000 / im.width))); b = io.BytesIO(); im.save(b, 'JPEG', quality=78)
    X = lambda t, inner: f'<?xml version="1.0" encoding="utf-8"?>\n<!DOCTYPE html>\n<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" lang="{code}" xml:lang="{code}" dir="{d}"><head><meta charset="utf-8"/><title>{E(t)}</title><link rel="stylesheet" type="text/css" href="style.css"/></head><body>{inner}</body></html>'
    files = [('cover', 'Capa', '<div class="cover"><img src="cover.jpg" alt="Wallace Ross"/></div>'),
             ('title', title, f'<section class="title"><div class="series">{E(m["series"])}</div><h1>{E(title)}</h1><div class="orn">✦</div><div class="author">Ailig Qarchi</div></section>')]
    for i, ch in enumerate(chs): files.append((f'c{i}', ch[1], body([ch])))
    files.append(('end', m['end_t'], endsec.replace('<br>', '<br/>')))
    ecss = 'body{margin:0 5%;line-height:1.55}p{margin:0;text-indent:1.3em;text-align:justify}p.first{text-indent:0}p.c{text-align:center;margin-bottom:1em}.cnum{text-align:center;font-size:.85em;letter-spacing:.2em;margin-top:2em;color:#555}h1,h2{text-align:center;font-weight:normal}h2{font-style:italic}.orn,.sep{text-align:center;color:#666;margin:.4em 0 1.4em}.title{text-align:center;padding-top:20%}.series{font-size:.85em;color:#555}.author{margin-top:2em;letter-spacing:.1em}.lic{font-size:.8em;color:#666}.cover{text-align:center;margin:0}.cover img{max-width:100%;height:100%}'
    nav = X('Index', '<nav epub:type="toc" id="toc"><ol>' + ''.join(f'<li><a href="{f[0]}.xhtml">{E(f[1])}</a></li>' for f in files[2:]) + '</ol></nav>')
    uid = str(uuid.uuid5(uuid.NAMESPACE_URL, f'ailigqarchi.com.br/wallace-ross/amostra/{code}'))
    now = datetime.datetime.now(datetime.UTC).strftime('%Y-%m-%dT%H:%M:%SZ')
    opf = f'''<?xml version="1.0" encoding="utf-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="bookid" xml:lang="{code}"><metadata xmlns:dc="http://purl.org/dc/elements/1.1/"><dc:identifier id="bookid">urn:uuid:{uid}</dc:identifier><dc:title>{E(title)} ({E(m["sample"])})</dc:title><dc:creator>Ailig Qarchi</dc:creator><dc:language>{code}</dc:language><dc:rights>{E(m["lic"])}</dc:rights><meta property="dcterms:modified">{now}</meta><meta name="cover" content="cover-img"/></metadata>
<manifest><item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/><item id="css" href="style.css" media-type="text/css"/><item id="cover-img" href="cover.jpg" media-type="image/jpeg" properties="cover-image"/>{"".join(f'<item id="{f[0]}" href="{f[0]}.xhtml" media-type="application/xhtml+xml"/>' for f in files)}</manifest>
<spine page-progression-direction="{d}">{"".join(f'<itemref idref="{f[0]}"/>' for f in files)}</spine></package>'''
    with zipfile.ZipFile(f'Wallace_Ross_amostra_{code}.epub', 'w') as z:
        z.writestr(zipfile.ZipInfo('mimetype'), 'application/epub+zip', compress_type=zipfile.ZIP_STORED)
        D = zipfile.ZIP_DEFLATED
        z.writestr('META-INF/container.xml', '<?xml version="1.0"?><container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container"><rootfiles><rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/></rootfiles></container>', D)
        z.writestr('OEBPS/content.opf', opf, D); z.writestr('OEBPS/nav.xhtml', nav, D); z.writestr('OEBPS/style.css', ecss, D); z.writestr('OEBPS/cover.jpg', b.getvalue(), D)
        for f in files: z.writestr(f'OEBPS/{f[0]}.xhtml', X(f[1], f[2]), D)
    print(code, 'ok')
