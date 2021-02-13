
function openFundCompany(evt, coid) {
  fetch(`/api/fundco/${coid}/position`)
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
    let position_change = "";
    if (p.enter_count > 0 || p.exit_count > 0) {
      position_change = `新进: <span style="color:#d50000">${p.enter_count}</span> 退出: <span style="color:green">${p.exit_count}</span>`
    }
    dataHTML += `<tr class="w3-hover-light-blue">
      <td><span style="display: inline-block; width: 80px;">${p.name}</span><span style="display: inline-block; color: gray;">${p.code}</span></td>
      <td>${p.volume_in_float}%</td>
      <td>${p.total_percent}%</td>
      <td>${p.funds.length}</td>
      <td>${position_change}</td>
    </tr>`;
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