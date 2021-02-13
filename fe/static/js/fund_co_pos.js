
window.onload = () => {
  openFundCompany(null, "80041198")
  document.getElementById("80041198").className += " w3-red";
}

let positionTableData;

function openFundCompany(evt, coid) {
  fetch(`/api/fundco/${coid}/position`)
    .then(response => response.json())
    .then(data => {
      positionTableData = data
      loadTableData(positionTableData)
    });
  if (evt) {
    tablinks = document.getElementsByClassName("tablink");
    for (i = 0; i < tablinks.length; i++) {
      tablinks[i].className = tablinks[i].className.replace(" w3-red", "");
    }
    evt.currentTarget.className += " w3-red";
  }
}

function loadTableData(data) {
  const tableBody = document.getElementById("table_data")
  let dataHTML = "";

  for (let p of data) {
    let positionChange = "";
    if (p.enter_count > 0 || p.exit_count > 0) {
      positionChange = `新进: <span style="color:#d50000">${p.enter_count}</span> 退出: <span style="color:green">${p.exit_count}</span>`
    }
    dataHTML += `<tr class="w3-hover-light-blue">
      <td><span style="display: inline-block; width: 80px;">${p.name}</span><span style="display: inline-block; color: gray;">${p.code}</span></td>
      <td>${p.volume_in_float}%</td>
      <td>${p.total_percent}%</td>
      <td>${p.funds.length}</td>
      <td>${positionChange}</td>
    </tr>`;
  }

  tableBody.innerHTML = dataHTML
}

let sortOptions = {
  volume_in_float: {
    direction: true,
    sortFunc: (dir) => sortNumberColumn("volume_in_float", dir),
  },
  total_percent: {
    direction: true,
    sortFunc: (dir) => sortNumberColumn("total_percent", dir),
  },
  fund_count: {
    direction: true,
    sortFunc: sortFundCount
  },
  position_change: {
    direction: false,
    sortFunc: sortPositionChange
  },
}

function sortColumn(columnName) {
  op = sortOptions[columnName]
  op.direction = !op.direction
  op.sortFunc(op.direction)

  loadTableData(positionTableData)
}

function sortNumberColumn(col, dir) {
  positionTableData = positionTableData.sort(
    (p1, p2) => {
      return dir ? p1[col] - p2[col] : p2[col] - p1[col]
    }
  );
}

function sortFundCount(dir) {
  positionTableData = positionTableData.sort(
    (p1, p2) => {
      return dir? p1.funds.length - p2.funds.length : p2.funds.length - p1.funds.length
    }
  );
}

function sortPositionChange(dir) {
  positionTableData = positionTableData.sort(
    (p1, p2) => {
      v1 = p1.enter_count * 1000 - p1.exit_count
      v2 = p2.enter_count * 1000 - p2.exit_count
      return dir? v1 - v2 : v2 - v1;
    }
  );
}
