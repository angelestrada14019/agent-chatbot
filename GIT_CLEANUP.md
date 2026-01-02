# 🧹 Guía: Eliminar Archivos .log del Historial de Git

## Problema

Ya hiciste commit de archivos `.log` y ahora están en el historial de Git. Aunque agregaste `*.log` al `.gitignore`, los archivos ya commiteados siguen siendo rastreados.

---

## ✅ Solución Paso a Paso

### Paso 1: Ver qué archivos .log están en Git

```bash
git ls-files | findstr .log
```

Esto muestra todos los `.log` que Git está rastreando.

### Paso 2: Eliminarlos del índice de Git (pero NO del disco)

```bash
# Eliminar UN archivo específico
git rm --cached mcp-server\mcp-server.log

# O eliminar TODOS los .log de una vez
git rm --cached -r *.log
```

**Importante**: `--cached` significa que solo se eliminan de Git, NO se borran de tu disco.

### Paso 3: Verificar .gitignore

Tu `.gitignore` debe tener:
```
_deprecated
.env
__pycache__
*.log
```

✅ Ya lo arreglé: cambié `.log` por `*.log`

### Paso 4: Hacer commit

```bash
git add .gitignore
git commit -m "Remove .log files from tracking and update .gitignore"
```

### Paso 5: Verificar que ya no están rastreados

```bash
git ls-files | findstr .log
```

Debería no retornar nada (o muy pocos archivos).

### Paso 6: Los archivos .log ahora deberían ser ignorados

```bash
git status
```

Los archivos `.log` **NO** deberían aparecer como "Untracked files".

---

## 🎯 Comando Todo-en-Uno

Si quieres hacerlo todo de una vez:

```bash
# 1. Eliminar todos los .log del índice
git rm --cached -r *.log

# 2. Commit el cambio
git add .gitignore
git commit -m "Remove .log files from tracking and update .gitignore"

# 3. Verificar
git status
```

---

## ⚠️ Alternativa: Si ya hiciste push

Si ya subiste los commits al repositorio remoto:

```bash
# 1. Eliminar del índice
git rm --cached -r *.log

# 2. Commit
git add .gitignore
git commit -m "Remove .log files from tracking"

# 3. Push (esto reescribe historial)
git push origin main
```

---

## 📋 Resumen Rápido

```bash
# Paso a paso:
git rm --cached -r *.log
git add .gitignore
git commit -m "Remove .log files from tracking and update .gitignore"
git status  # Verificar que funcionó
```

**¡Listo!** Los archivos `.log` ya no serán rastreados por Git.

---

## 🔍 Notas Importantes

1. **Los archivos NO se borran** del disco, solo dejan de ser rastreados
2. **No afecta commits anteriores** - solo futuros commits
3. **Otros desarrolladores** necesitarán hacer `git pull` para actualizar
4. **Archivos `.log` locales** seguirán existiendo, pero Git los ignorará

---

## ✅ .gitignore Correcto

```
_deprecated
.env
__pycache__
*.log       # ← Esto ignora TODOS los .log
logs/       # ← Opcional: ignorar carpeta completa
temp/
exports/
```

**Archivo actualizado:** ✅ Ya cambié `.log` → `*.log` en tu `.gitignore`
