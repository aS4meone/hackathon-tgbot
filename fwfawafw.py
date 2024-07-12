from copydetect import CopyDetector

detector = CopyDetector(test_dirs=["tests"], extensions=["py"], display_t=0.5)
detector.add_file("app/utils/llm.py")
detector.run()
detector.generate_html_report()
