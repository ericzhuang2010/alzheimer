## On Minerva

You do **not** need to install R or manually edit `PATH`. Minerva manages R through **Lmod environment modules**; loading the R module adds `R` and `Rscript` to your command-line environment. Minerva recommends selecting an explicit version for reproducibility because the default version can change. ([labs.icahn.mssm.edu](https://labs.icahn.mssm.edu/minervalab/documentation/r/))

### 1. Find the installed R versions

After logging into Minerva, run:

```bash
module -r spider '^R$'
```

Use the straight ASCII quotation marks shown above, not curly “smart quotes.”

A less restrictive search is:

```bash
ml spider R
```

### 2. Load R

To load Minerva’s current default version:

```bash
module load R
```

The shorter equivalent is:

```bash
ml R
```

For reproducible analyses, select one of the exact versions returned by `module spider`, for example:

```bash
module load R/4.2.0
```

Here, `4.2.0` is only the example shown in the documentation; use a version currently listed on Minerva rather than assuming that this older example is still the preferred version. ([labs.icahn.mssm.edu](https://labs.icahn.mssm.edu/minervalab/documentation/r/))

### 3. Confirm that both commands are available

```bash
command -v R
command -v Rscript

R --version
Rscript --version
```

You should now see filesystem paths for both executables and their version information.

### 4. Start interactive R

For actual computation, Minerva’s documentation says to obtain an interactive LSF compute session first rather than doing substantial work on a login node:

```bash
bsub -q interactive \
     -P acc_YOURPROJECT \
     -n 1 \
     -W 1:00 \
     -R 'rusage[mem=8000]' \
     -Is /bin/bash
```

Replace `acc_YOURPROJECT` with your Minerva allocation. Once the compute-node prompt appears:

```bash
module load R
R
```

Inside R:

```r
print("Hello World!", quote = FALSE)
```

Exit with:

```r
q()
```

The documentation’s example includes `-XF`, which is for X11 forwarding; ordinary command-line R does not generally need it. ([labs.icahn.mssm.edu](https://labs.icahn.mssm.edu/minervalab/documentation/r/))

### 5. Run an R script

Create a test script:

```bash
cat > hello.R <<'EOF'
print("Hello World!", quote = FALSE)
EOF
```

Run it:

```bash
Rscript hello.R
```

Expected output:

```text
[1] Hello World!
```

The documented syntax is:

```bash
Rscript [options] your_script.R
```

([labs.icahn.mssm.edu](https://labs.icahn.mssm.edu/minervalab/documentation/r/))

## Important: load R in every new session or job

`module load R` changes the environment of the **current shell**. Therefore, after a new login, inside a new interactive compute job, or inside a batch job, load the module again.

A basic batch-job script could look like this:

```bash
#!/bin/bash
#BSUB -J r_analysis
#BSUB -P acc_YOURPROJECT
#BSUB -q YOUR_QUEUE
#BSUB -n 1
#BSUB -W 01:00
#BSUB -R "rusage[mem=8000]"
#BSUB -o r_analysis.%J.out
#BSUB -e r_analysis.%J.err

module purge
module load R
Rscript analysis.R
```

Submit it with:

```bash
bsub < run_r.sh
```

Once you have selected a stable version, replace `module load R` in job scripts with an explicit command such as `module load R/4.x.y`. This prevents a future change to Minerva’s default R module from unexpectedly changing your analysis environment. ([labs.icahn.mssm.edu](https://labs.icahn.mssm.edu/minervalab/documentation/r/))

The essential setup is therefore:

```bash
module -r spider '^R$'
module load R
R
# or:
Rscript your_script.R
```

## Command I use
module load R/4.3.3