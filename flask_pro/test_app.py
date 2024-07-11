from flask import Flask, request, Response, stream_with_context, session, render_template_string
import sys
import traceback
import io

app = Flask(__name__)
app.secret_key = 'your_secret_key'


@app.route('/')
def index():
    # Render a simple HTML form to input Python code
    return render_template_string('''
        <!doctype html>
        <html>
        <head>
            <title>Execute Python Code</title>
            <script>
                function submitCode() {
                    const code = document.getElementById('code').value;
                    const eventSource = new EventSource('/submit?code=' + encodeURIComponent(code));
                    eventSource.onmessage = function(event) {
                        const resultDiv = document.getElementById('result');
                        resultDiv.innerHTML += event.data + "<br>";
                    };
                    eventSource.onerror = function() {
                        eventSource.close();
                    };
                }
            </script>
        </head>
        <body>
            <h1>Execute Python Code</h1>
            <textarea id="code" rows="10" cols="30"></textarea><br>
            <button onclick="submitCode()">Execute</button>
            <div id="result"></div>
        </body>
        </html>
    ''')


@app.route('/submit')
def submit():
    data = request.args.get('code')  # 获取代码

    session_modifications = []

    def generate(data):
        original_stdout = sys.stdout
        output = io.StringIO()
        sys.stdout = output

        # Split the code into lines
        code_lines = data.split('\n')

        for line in code_lines:
            if 'session' in line:
                session_modifications.append(line)
            else:
                try:
                    # Execute the line if it doesn't modify the session
                    exec(line, {'session': session, **globals()})
                except Exception as e:
                    exc_info = traceback.format_exc()
                    if session.get('template') == True:
                        yield f"An error occurred: {repr(e)}\n{exc_info}"
                    else:
                        yield "Nothing can I get! Please change an area and search again :)"
                finally:
                    sys.stdout = original_stdout

                code_result = str(output.getvalue().replace('\00', ''))
                output.truncate(0)
                output.seek(0)
                yield code_result

    def event_stream(data):
        # Generate code execution output
        for result in generate(data):
            yield f"data: {result}\n\n"

        # Execute session modifications and send the results
        original_stdout = sys.stdout
        output = io.StringIO()
        sys.stdout = output

        with app.app_context():
            for line in session_modifications:
                try:
                    exec(line, {'session': session, **globals()})
                except Exception as e:
                    exc_info = traceback.format_exc()
                    yield f"data: An error occurred in session modification: {repr(e)}\n{exc_info}\n\n"

        sys.stdout = original_stdout
        session_result = str(output.getvalue().replace('\00', ''))
        yield f"data: {session_result}\n\n"

    response = Response(stream_with_context(event_stream(data)), content_type='text/event-stream')
    return response


if __name__ == '__main__':
    app.run(debug=True)
