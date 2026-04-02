#!/usr/bin/env python3
"""
arcanus-bugfix-tests.py
Test de exploración — Bug A: goToSelect roto desde instrucciones
Property 1: Bug Condition — goToSelect falla cuando title-screen está oculto

CRITICAL: Este test DEBE FALLAR en el código sin fix.
El fallo confirma que el bug existe.
DO NOT attempt to fix the test or the code when it fails.

Validates: Requirements 1.1, 2.1

Análisis del bug real:
  - #sel-screen:   z-index: 50
  - #inst-screen:  z-index: 75
  - #title-screen: z-index: 80

  Cuando goToSelect() se llama desde instrucciones:
  1. title-screen ya tiene display:none (ocultado por goToInstructions())
  2. ts.classList.add('hide') — no produce animación visible (display:none)
  3. setTimeout(580ms) ejecuta: ts.style.display='none' (ya era none)
     y sel-screen.style.display='block' ← sel-screen SÍ recibe display:block
  4. PERO inst-screen sigue con display:block y z-index:75 > z-index:50
     → inst-screen TAPA a sel-screen → el usuario no ve sel-screen

  La condición de bug correcta es:
    isBugConditionA = title_screen.style.display === 'none'
                      AND inst_screen.style.display === 'block' (o classList.contains('show'))
                      AND después de goToSelect():
                          inst_screen.style.display !== 'none'  ← inst-screen NO se oculta
"""

import time
import threading

# ─────────────────────────────────────────────────────────────────────────────
# Simulación mínima del DOM (suficiente para goToSelect)
# ─────────────────────────────────────────────────────────────────────────────

class Style:
    def __init__(self, display=''):
        self.display = display

class ClassList:
    def __init__(self):
        self._classes = set()
    def add(self, cls):
        self._classes.add(cls)
    def remove(self, cls):
        self._classes.discard(cls)
    def contains(self, cls):
        return cls in self._classes
    def __str__(self):
        return ' '.join(sorted(self._classes))

class DOMElement:
    def __init__(self, element_id, initial_display=''):
        self.id = element_id
        self.style = Style(initial_display)
        self.classList = ClassList()

class FakeDocument:
    def __init__(self):
        self._elements = {}
    def register(self, el):
        self._elements[el.id] = el
    def getElementById(self, eid):
        return self._elements.get(eid)

# ─────────────────────────────────────────────────────────────────────────────
# Función bajo test — extraída de Arcanus_V9.html (sin modificar)
# ─────────────────────────────────────────────────────────────────────────────

def make_goToSelect(document):
    """Implementación original de goToSelect() sin ningún fix."""
    def goToSelect():
        ts = document.getElementById('title-screen')
        ts.classList.add('hide')
        def _after():
            ts.style.display = 'none'
            document.getElementById('sel-screen').style.display = 'block'
        t = threading.Timer(0.580, _after)
        t.start()
        return t
    return goToSelect

def make_goToInstructions(document):
    """Implementación original de goToInstructions() sin ningún fix."""
    def goToInstructions():
        document.getElementById('title-screen').style.display = 'none'
        ins = document.getElementById('inst-screen')
        ins.style.display = 'block'
        ins.classList.add('show')
    return goToInstructions

# ─────────────────────────────────────────────────────────────────────────────
# Mini test runner
# ─────────────────────────────────────────────────────────────────────────────

RESET  = '\033[0m'
RED    = '\033[91m'
GREEN  = '\033[92m'
YELLOW = '\033[93m'
CYAN   = '\033[96m'
BOLD   = '\033[1m'

results = []

def assert_test(description, condition, detail=''):
    results.append({'description': description, 'pass': condition, 'detail': detail})
    status = f'{GREEN}✓ PASS{RESET}' if condition else f'{RED}✗ FAIL{RESET}'
    print(f'  {status}  {description}')
    if detail:
        print(f'         {YELLOW}{detail}{RESET}')

def suite_title(title):
    print(f'\n{CYAN}{BOLD}{title}{RESET}')
    print('─' * 70)

# ─────────────────────────────────────────────────────────────────────────────
# SUITE 1 — Bug A: goToSelect() desde instrucciones
# Property 1: Bug Condition — goToSelect falla cuando title-screen está oculto
# Validates: Requirements 1.1, 2.1
#
# El bug real: inst-screen NO se oculta cuando goToSelect() se llama desde
# instrucciones. sel-screen recibe display:block pero queda tapado por
# inst-screen (z-index:75 > z-index:50).
# ─────────────────────────────────────────────────────────────────────────────

print(f'\n{BOLD}✦ ARCANUS — BUGFIX TESTS{RESET}')
print('=' * 70)

suite_title('SUITE 1 — Bug A: goToSelect() desde instrucciones (Property 1: Bug Condition)')
print(f'{YELLOW}Simulando flujo real: título → instrucciones → goToSelect()...{RESET}')

# Crear DOM fresco
doc = FakeDocument()
title_screen = DOMElement('title-screen', initial_display='flex')
inst_screen  = DOMElement('inst-screen',  initial_display='none')
sel_screen   = DOMElement('sel-screen',   initial_display='none')
doc.register(title_screen)
doc.register(inst_screen)
doc.register(sel_screen)

# Paso 1: Simular goToInstructions() — el usuario navega a instrucciones
goToInstructions = make_goToInstructions(doc)
goToInstructions()

# Verificar estado post-instrucciones
assert_test(
    'Precondición: title-screen.style.display === "none" (después de goToInstructions)',
    title_screen.style.display == 'none',
    f'Actual: "{title_screen.style.display}"'
)
assert_test(
    'Precondición: inst-screen.style.display === "block" (después de goToInstructions)',
    inst_screen.style.display == 'block',
    f'Actual: "{inst_screen.style.display}"'
)
assert_test(
    'Precondición: inst-screen tiene clase "show" (después de goToInstructions)',
    inst_screen.classList.contains('show'),
    f'classList: "{inst_screen.classList}"'
)

# Paso 2: El usuario hace clic en "¡Jugar ahora! ✦" → llama goToSelect()
goToSelect = make_goToSelect(doc)
timer = goToSelect()
time.sleep(0.700)  # esperar 700ms (más que el timeout de 580ms)

# ─── TESTS PRINCIPALES ───
# El bug real: inst-screen NO se oculta → tapa a sel-screen
inst_display_after = inst_screen.style.display
sel_display_after  = sel_screen.style.display
ts_display_after   = title_screen.style.display

# Test 1: sel-screen SÍ recibe display:block (el setTimeout ejecuta)
# Este test PASA — sel-screen sí se muestra en el DOM
assert_test(
    'sel-screen.style.display === "block" después de 700ms (setTimeout ejecuta)',
    sel_display_after == 'block',
    f'Actual: "{sel_display_after}"'
)

# Test 2: ESTE TEST DEBE FALLAR — inst-screen NO se oculta
# El bug: goToSelect() no oculta inst-screen, que queda con display:block
# y z-index:75 > z-index:50 de sel-screen → inst-screen TAPA a sel-screen
assert_test(
    'Bug A — inst-screen.style.display === "none" después de goToSelect() (DEBE FALLAR en código sin fix)',
    inst_display_after == 'none',
    f'Actual: "{inst_display_after}" — CONTRAEJEMPLO: goToSelect() desde instrucciones → '
    f'inst-screen permanece visible (display:"{inst_display_after}") y tapa a sel-screen '
    f'(z-index:75 > z-index:50). El usuario no puede ver sel-screen.'
)

# Test 3: inst-screen NO debe tener clase 'show' después de goToSelect()
assert_test(
    'Bug A — inst-screen NO tiene clase "show" después de goToSelect() (DEBE FALLAR en código sin fix)',
    not inst_screen.classList.contains('show'),
    f'classList: "{inst_screen.classList}" — inst-screen sigue con clase "show"'
)

# ─────────────────────────────────────────────────────────────────────────────
# SUITE 2 — goToSelect() desde título (comportamiento de referencia)
# ─────────────────────────────────────────────────────────────────────────────

suite_title('SUITE 2 — goToSelect() desde título (comportamiento de referencia)')
print(f'{YELLOW}Configurando estado desde título y llamando goToSelect()...{RESET}')

doc2 = FakeDocument()
title_screen2 = DOMElement('title-screen', initial_display='flex')
inst_screen2  = DOMElement('inst-screen',  initial_display='none')
sel_screen2   = DOMElement('sel-screen',   initial_display='none')
doc2.register(title_screen2)
doc2.register(inst_screen2)
doc2.register(sel_screen2)

# Estado desde título: title-screen visible, inst-screen oculto
assert_test(
    'Precondición: title-screen.style.display === "flex" (estado desde título)',
    title_screen2.style.display == 'flex',
    f'Actual: "{title_screen2.style.display}"'
)
assert_test(
    'Precondición: inst-screen.style.display === "none" (no se visitaron instrucciones)',
    inst_screen2.style.display == 'none',
    f'Actual: "{inst_screen2.style.display}"'
)

goToSelect2 = make_goToSelect(doc2)
timer2 = goToSelect2()
time.sleep(0.700)

assert_test(
    'Desde título — sel-screen.style.display === "block" después de 700ms (debe pasar)',
    sel_screen2.style.display == 'block',
    f'Actual: "{sel_screen2.style.display}"'
)
assert_test(
    'Desde título — title-screen.style.display === "none" después de goToSelect()',
    title_screen2.style.display == 'none',
    f'Actual: "{title_screen2.style.display}"'
)
# Desde título, inst-screen ya estaba oculto — no hay problema de tapado
assert_test(
    'Desde título — inst-screen.style.display === "none" (no tapa a sel-screen)',
    inst_screen2.style.display == 'none',
    f'Actual: "{inst_screen2.style.display}"'
)

# ─────────────────────────────────────────────────────────────────────────────
# Resumen y contraejemplo
# ─────────────────────────────────────────────────────────────────────────────

total  = len(results)
passed = sum(1 for r in results if r['pass'])
failed = total - passed

print('\n' + '=' * 70)
print(f'{BOLD}Resultados: {passed}/{total} pasaron — {failed} fallaron{RESET}')

failed_tests = [r for r in results if not r['pass']]
if failed_tests:
    print(f'\n{YELLOW}{BOLD}⚠ CONTRAEJEMPLO DOCUMENTADO (confirma que el bug existe):{RESET}')
    print()
    print(f'{YELLOW}Condición de bug (isBugConditionA):{RESET}')
    print('  • title_screen.style.display === "none"  (title-screen ya estaba oculto)')
    print('  • inst_screen.classList.contains("show") === True  (instrucciones visibles)')
    print()
    print(f'{YELLOW}Comportamiento observado tras goToSelect():{RESET}')
    print(f'  • sel-screen.style.display = "{sel_display_after}"  (el setTimeout sí ejecuta)')
    print(f'  • inst-screen.style.display = "{inst_display_after}"  ← BUG: inst-screen NO se oculta')
    print(f'  • inst-screen.classList = "{inst_screen.classList}"  ← BUG: clase "show" no se remueve')
    print()
    print(f'{YELLOW}Causa raíz:{RESET}')
    print('  • goToSelect() NO oculta inst-screen antes de mostrar sel-screen.')
    print('  • inst-screen tiene z-index:75, sel-screen tiene z-index:50.')
    print('  • inst-screen (visible, z-index:75) TAPA a sel-screen (z-index:50).')
    print('  • El usuario ve instrucciones en lugar de la pantalla de selección.')
    print()
    print(f'{YELLOW}Comportamiento esperado (tras el fix):{RESET}')
    print('  • goToSelect() debe ocultar inst-screen: classList.remove("show") + style.display="none"')
    print('  • Luego mostrar sel-screen directamente (sin esperar 580ms si title-screen ya está oculto)')
    print()
    print(f'{YELLOW}Tests fallidos:{RESET}')
    for t in failed_tests:
        print(f'  • {t["description"]}')
        if t['detail']:
            print(f'    {t["detail"]}')
    print()
    import sys
    sys.exit(1)
else:
    print(f'\n{GREEN}✓ Todos los tests pasaron — El bug no se reproduce (posible fix ya aplicado){RESET}')
