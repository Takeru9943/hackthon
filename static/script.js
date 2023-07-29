let dots = 0;
const statusElement = document.getElementById('upload-status');

function updateDots() {
  dots = (dots + 1) % 6;
  const dotString = '.'.repeat(dots);
  statusElement.innerText = dots === 5 ? 'Analyzing now' : `Analyzing now${dotString}`;
}

function changeStatus() {
  statusElement.innerText = 'Analyzing now';
  setInterval(updateDots, 1000); // 1000ms (1秒)ごとにupdateDots関数を呼び出す
}