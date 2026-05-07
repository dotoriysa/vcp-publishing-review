"""
퍼블리싱 코드 자동 검수 도구 - Flask 웹 서버
"""
import os
import zipfile
import tempfile
from flask import Flask, render_template, request, jsonify
from src.reviewer import Reviewer

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 최대 500MB


@app.route('/')
def index():
    """메인 페이지"""
    return render_template('index.html')


@app.route('/review', methods=['POST'])
def review():
    """검수 실행 API"""
    if 'file' not in request.files:
        return jsonify({'error': '파일이 없습니다'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': '파일을 선택해주세요'}), 400

    if not file.filename.endswith('.zip'):
        return jsonify({'error': 'ZIP 파일만 업로드 가능합니다'}), 400

    # 선택된 규칙
    selected_rules = request.form.getlist('rules')
    if not selected_rules:
        selected_rules = ['typography', 'color', 'important', 'scrollbar']

    # 임시 폴더에 저장 후 검수
    with tempfile.TemporaryDirectory() as tmp_dir:
        zip_path = os.path.join(tmp_dir, 'upload.zip')
        file.save(zip_path)

        try:
            reviewer = Reviewer(zip_path, selected_rules)
            report = reviewer.run()
            return jsonify(report)
        except zipfile.BadZipFile:
            return jsonify({'error': '올바른 ZIP 파일이 아닙니다'}), 400
        except Exception as e:
            return jsonify({'error': f'검수 중 오류 발생: {str(e)}'}), 500


if __name__ == '__main__':
    print("퍼블리싱 코드 검수 도구를 시작합니다...")
    print("브라우저에서 http://localhost:5000 을 열어주세요")
    app.run(debug=True, port=5000)
