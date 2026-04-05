Build the PDF (requires MiKTeX / TeX Live, or use Overleaf):

  cd Proj/report
  powershell -ExecutionPolicy Bypass -File build_pdf.ps1

Or manually:

  pdflatex progress_report_acl.tex
  pdflatex progress_report_acl.tex

Or zip the report folder (include figures/ and generated_numbers.tex) and upload to Overleaf.

Regenerate numbers and figures after changing code:

  cd Proj
  pip install -r requirements.txt
  python run_preliminary_benchmark.py

This overwrites report/generated_numbers.tex and report/figures/*.png.
