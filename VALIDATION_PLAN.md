# 🎯 ACTION PLAN - Verify & Test Fixes

## 📋 Current Status

✅ **Diagnostic Complete** - Issues identified  
✅ **Fixes Implemented** - 3 critical fixes applied  
⏳ **Next: Validate Fixes** - Your turn!

---

## 🚀 Validation Steps (30 minutes)

### **Step 1: Verify Code Changes Were Applied** (5 min)

```bash
# Check Fix #1: Inverse affine in apply_affine.py
echo "=== Checking Fix #1 ==="
grep "affine_inv = np.linalg.inv" /mnt/c/Users/ADMIN/Desktop/MRI/alzheimer/tools/CorticalFlow/scripts/apply_affine.py
# Expected: Should show the line with np.linalg.inv

# Check Fix #2: Removed cropping from data.py
echo "=== Checking Fix #2 ==="
grep "hemisphere constraint is enforced by template mesh" /mnt/c/Users/ADMIN/Desktop/MRI/alzheimer/tools/CorticalFlow/src/data.py
# Expected: Should show the message

# Check Fix #3: Debug output in recon_all.sh
echo "=== Checking Fix #3 ==="
grep "DEBUG.*Affine matrix" /mnt/c/Users/ADMIN/Desktop/MRI/alzheimer/tools/CorticalFlow/recon_all.sh
# Expected: Should show debug echo command
```

### **Step 2: Backup ADNI Results (to compare before/after)** (2 min)

```bash
cd /mnt/c/Users/ADMIN/Desktop/MRI/alzheimer

# The reprocess script does this automatically, but manual backup helps
mkdir -p comparison_backup
cp -r pipeline-subjects/I776974/surf comparision_backup/surf_old
cp pipeline-subjects/I776974/mri/transforms/reg_affine.txt comparison_backup/reg_affine_old.txt 2>/dev/null || true

echo "✓ Backup created in comparison_backup/"
```

### **Step 3: Reprocess ADNI with Fixes** (5-10 min)

```bash
cd /mnt/c/Users/ADMIN/Desktop/MRI/alzheimer

# Make script executable
chmod +x reprocess_adni_step5.sh

# Run it!
bash reprocess_adni_step5.sh

# This will:
# 1. Backup old surfaces
# 2. Delete old temporary files  
# 3. Run recon_all.sh with fixes
# 4. Save detailed log
```

**What to watch for during execution:**
```
[INFO] Should see CorticalFlow messages
[INFO] Should see "[DEBUG] Affine matrix" in output
[INFO] Should see "Mapping surfaces back to native space"
[INFO] Should see "Moving surfaces to /path/to/surf/"
[INFO] Process should complete without errors
```

### **Step 4: Check Log File** (3 min)

```bash
# View the reprocessing log
cat /mnt/c/Users/ADMIN/Desktop/MRI/alzheimer/pipeline-subjects/I776974/step5_reprocess.log

# Look for:
grep "ERROR" pipeline-subjects/I776974/step5_reprocess.log
# Should find NONE

grep "DEBUG" pipeline-subjects/I776974/step5_reprocess.log
# Should show affine matrix debug info
```

### **Step 5: Run Diagnostic Again** (5 min)

```bash
python /mnt/c/Users/ADMIN/Desktop/MRI/alzheimer/debug_adni_surface_alignment.py

# Save output for comparison
python /mnt/c/Users/ADMIN/Desktop/MRI/alzheimer/debug_adni_surface_alignment.py > /tmp/adni_diagnostic_after_fixes.txt 2>&1

# View key sections
echo "=== ADNI Surface Bounds AFTER FIXES ===" 
cat /tmp/adni_diagnostic_after_fixes.txt | grep -A 4 "ADNI Subject I776974 - Surfaces"
```

### **Step 6: Compare Before vs After** (5 min)

```bash
# Expected: ADNI bounds should now be MUCH CLOSER to OASIS

# BEFORE (from your diagnostic):
echo "BEFORE FIXES:"
echo "ADNI lh.white Y: [-86.1, 100.8] (range 186.9)"
echo "OASIS lh.white Y: [-85.4, 56.4] (range 141.8)"
echo "Difference: 45.1 mm ❌"

# AFTER (run diagnostic again):
python /mnt/c/Users/ADMIN/Desktop/MRI/alzheimer/debug_adni_surface_alignment.py | tail -30

# Look for results like:
echo ""
echo "AFTER FIXES (EXPECTED):"
echo "ADNI lh.white Y: ~[-85.6, 56.8] (range ~142)"
echo "OASIS lh.white Y: [-85.4, 56.4] (range 141.8) "
echo "Difference: <2 mm ✓"
```

### **Step 7: Visual Verification in FreeView** (5 min)

```bash
# Open FreeView comparison
echo "Opening FreeView - compare OASIS vs ADNI..."

# Terminal 1: OASIS
freeview /mnt/c/Users/ADMIN/Desktop/MRI/alzheimer/pipeline-subjects/0006/mri/orig.mgz \
         /mnt/c/Users/ADMIN/Desktop/MRI/alzheimer/pipeline-subjects/0006/surf/lh.white:edgecolor=red \
         /mnt/c/Users/ADMIN/Desktop/MRI/alzheimer/pipeline-subjects/0006/surf/lh.pial:edgecolor=blue &

# Wait a moment, then Terminal 2: ADNI
freeview /mnt/c/Users/ADMIN/Desktop/MRI/alzheimer/pipeline-subjects/I776974/mri/orig.mgz \
         /mnt/c/Users/ADMIN/Desktop/MRI/alzheimer/pipeline-subjects/I776974/surf/lh.white:edgecolor=red \
         /mnt/c/Users/ADMIN/Desktop/MRI/alzheimer/pipeline-subjects/I776974/surf/lh.pial:edgecolor=blue &

sleep 3
echo "FreeView windows should open..."
```

**What to look for:**
- ✓ Red outline (lh.white) aligns with brain white matter
- ✓ Blue outline (lh.pial) aligns with brain edge/pial surface
- ✓ Both hemispheres look anatomically reasonable
- ✓ ADNI should look similar to OASIS
- ❌ If surfaces are floating away or upside-down → Still a problem

---

## ✅ Success Criteria

Your fixes are **SUCCESSFUL** if:

- [ ] Diagonal runs without errors
- [ ] ADNI surface Y bounds now **similar to OASIS** (within 5mm)
- [ ] ADNI surface Z bounds now **similar to OASIS** (within 5mm)
- [ ] FreeView shows surfaces aligned with brain
- [ ] Log file has no ERROR messages
- [ ] All 4 surface files exist: lh.white, lh.pial, rh.white, rh.pial

---

## 🔍 If Something Goes Wrong

### **Issue: Script fails during reprocessing**

```bash
# Check the log
tail -50 /mnt/c/Users/ADMIN/Desktop/MRI/alzheimer/pipeline-subjects/I776974/step5_reprocess.log

# If error about Python/libraries:
source /mnt/c/Users/ADMIN/Desktop/MRI/alzheimer/tools/CorticalFlow/cortical-flow/bin/activate

# Then retry
bash /mnt/c/Users/ADMIN/Desktop/MRI/alzheimer/reprocess_adni_step5.sh
```

### **Issue: Surfaces still misaligned after fixes**

Then the problem is different than identified. Possible solutions:

1. **Revert to simpler fix** - Try using forward affine again (to see if issue is elsewhere)
2. **Check NiftyReg** - Maybe affine registration itself is poor (check Scale factors)
3. **Check MRI input** - Verify ADNI MRI is correct after preprocessing

Command to revert apply_affine.py:
```bash
# Change inverted back to forward
sed -i 's/affine_inv = np.linalg.inv(affine_matrix)/# affine_inv = np.linalg.inv(affine_matrix)/g' \
    tools/CorticalFlow/scripts/apply_affine.py
sed -i 's/np.matmul(affine_inv, vertices.T)/np.matmul(affine_matrix, vertices.T)/g' \
    tools/CorticalFlow/scripts/apply_affine.py
```

---

## 📊 Expected Output Samples

### Diagnostic BEFORE Fixes (what you saw):
```
ADNI lh.white Y: [-86.1, 100.8] (range 186.9)
OASIS lh.white Y: [-85.4, 56.4] (range 141.8)
Scale difference: 0.115407 ❌
```

### Diagnostic AFTER Fixes (what to expect):
```
ADNI lh.white Y: ~[-86.2, 56.1] (range ~142.3)
OASIS lh.white Y: [-85.4, 56.4] (range 141.8)
Scale difference: ~0.005 ✓  (much better!)
```

---

## 🚀 Next After Validation

If fixes pass validation:

1. **Run Steps 6-8:**
```bash
python /mnt/c/Users/ADMIN/Desktop/MRI/alzheimer/main.py
```

2. **Compare stats:**
```bash
# Check parcellation stats
head pipeline-subjects/I776974/stats/lh.aparc.stats

# Check thickness measurements
head pipeline-subjects/I776974/lh.schaefer2018_200_7.thickness.mine.txt
```

3. **Compare OASIS vs ADNI results** to verify consistency

---

## 📝 Keep Track

Save this for reference:
```bash
# Before fixes
cat > /tmp/adni_before_fixes.txt << 'EOF'
ADNI lh.white bounds Y: [-86.1, 100.8]
ADNI lh.white bounds Z: [-20.3, 88.6]
Scale factor: 0.972
EOF

# After fixes
python debug_adni_surface_alignment.py > /tmp/adni_after_fixes.txt 2>&1
grep "ADNI Subject I776974" /tmp/adni_after_fixes.txt -A 20
```

---

## 💬 Questions to Ask

If issues persist, provide:

1. Content of `/tmp/adni_diagnostic_after_fixes.txt`
2. Content of `pipeline-subjects/I776974/step5_reprocess.log`
3. Screenshot of FreeView comparison
4. Output of specific diagnostic commands

---

**You're ~70% done with the fix! Just need to:**
1. ✅ Run reprocess_adni_step5.sh  
2. ✅ Run diagnostics again
3. ✅ Compare results

**Let me know if it works!** 🎯
