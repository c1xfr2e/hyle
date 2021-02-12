
function openFundCompany(evt, coid) {
  fetch(`http://127.0.0.1:5000//fundco/${coid}/position`)
    .then(response => response.json())
    .then(data => {
      positionData = data
      loadTableData(positionData)
    });
  if (evt) {
    tablinks = document.getElementsByClassName("tablink");
    for (i = 0; i < tablinks.length; i++) {
      tablinks[i].className = tablinks[i].className.replace(" w3-red", "");
    }
    evt.currentTarget.className += " w3-red";
  }
}

let sortDirection = true;

let positionData;

window.onload = () => {
  openFundCompany(null, "80041198")
  document.getElementById("80041198").className += " w3-red";
}

function loadTableData(positionData) {
  const tableBody = document.getElementById("table_data")
  let dataHTML = "";

  for (let p of positionData) {
    dataHTML += `<tr class="w3-hover-light-blue">
      <td><span style="display: inline-block; width: 80px;">${p.name}</span><span style="display: inline-block; color: gray;">${p.code}</span></td>
      <td>${p.total_percent}%</td>
      <td>${p.volume_in_float}%</td>
      <td>${p.fund_count}</td>
    </tr>`
  }

  tableBody.innerHTML = dataHTML
}

function sortColumn(columnName) {
  const dataType = typeof positionData[0][columnName];
  sortDirection = !sortDirection

  switch (dataType) {
    case "number":
      sortNumberColumn(sortDirection, columnName);
      break;
  }

  loadTableData(positionData)

  th = document.getElementById(columnName)

}

function sortNumberColumn(dir, col) {
  positionData = positionData.sort(
    (p1, p2) => {
      return dir ? p1[col] - p2[col] : p2[col] - p1[col]
    }
  );
}