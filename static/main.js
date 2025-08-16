$(document).ready(function () {
  $("#show-signup").on("click", function (e) {
    e.preventDefault();
    $("#login-form").hide();
    $("#signup-form").show();
    $("#form-title").text("Sign Up");
    $("#form-toggle").html(
      'Already have an account? <a href="#" id="show-login">Login</a>'
    );
  });

  $(document).on("click", "#show-login", function (e) {
    e.preventDefault();
    $("#signup-form").hide();
    $("#login-form").show();
    $("#form-title").text("Login");
    $("#form-toggle").html(
      'Don\'t have an account? <a href="#" id="show-signup">Sign Up</a>'
    );
  });

  // Signup form submission
  $("#signup-form").on("submit", function (e) {
    e.preventDefault();

    const formData = {
      username: $("#signup-form input[name='username']").val().trim(),
      password: $("#signup-form input[name='password']").val().trim(),
    };

    $("#message").text("");

    if (!formData.username || !formData.password) {
      $("#message")
        .css("color", "red")
        .text("Username and password are required.");
      return;
    }

    // Signup AJAX
    $.ajax({
      url: "/cgi-bin/app.py?action=signup",
      method: "POST",
      data: formData,
      dataType: "json",
      success: function (res) {
        if (res.success) {
          $("#message")
            .css("color", "green")
            .text("Signup successful! Logging in...");

          // Auto-login
          $.ajax({
            url: "/cgi-bin/app.py?action=login",
            method: "POST",
            data: formData,
            dataType: "json",
            success: function (loginRes) {
              if (loginRes.success) {
                window.location.href = "/cgi-bin/app.py?action=dashboard";
              } else {
                $("#message")
                  .css("color", "red")
                  .text("Login failed after signup.");
              }
            },
            error: function (xhr, status, error) {
              $("#message")
                .css("color", "red")
                .text("Login failed after signup due to server error.");
            },
          });
        } else {
          $("#message").css("color", "red").text(res.message);
        }
      },
      error: function (xhr, status, error) {
        $("#message")
          .css("color", "red")
          .text("Signup failed due to server error.");
      },
    });
  });

  $("#login-form").on("submit", function (e) {
    e.preventDefault();

    const formData = {
      username: $("input[name='username']").val(),
      password: $("input[name='password']").val(),
    };

    $.ajax({
      url: "/cgi-bin/app.py?action=login",
      method: "POST",
      data: formData,
      dataType: "json",
      success: function (response) {
        if (response.success) {
          window.location.href = "app.py?action=dashboard";
        } else {
          $("#message").html(response.message);
        }
      },
      error: function (xhr, status, error) {
        console.log("AJAX Error:", status, error, xhr.responseText);
        $("#message").html("Error: Could not parse server response.");
      },
    });
  });

  $("#show-add-form").click(function () {
    $("#add-item-form").toggle();
    $("#add-item-form")[0].scrollIntoView({ behavior: "smooth" });
  });

  function fetchItems() {
    $.getJSON("/cgi-bin/app.py?action=list", function (items) {
      let html = "<table border='1' cellpadding='6'>";
      html +=
        "<tr><th>ID</th><th>Name</th><th>Description</th><th>Price</th><th>Actions</th></tr>";

      if (!items || items.length === 0) {
        html += "<tr><td colspan='5'>No items found</td></tr>";
      } else {
        items.forEach((i) => {
          html += `<tr data-id="${i.id}">
            <td>${i.id}</td>
            <td class="name">${i.name}</td>
            <td class="description">${i.description}</td>
            <td class="price">${i.price.toFixed(2)}</td>
            <td>
              <button class="edit-btn" data-id="${i.id}">Edit</button>
              <button class="delete-btn" data-id="${i.id}">Delete</button>
            </td>
        </tr>`;
        });
      }

      html += "</table>";
      $("#items-list").html(html);
    }).fail(function (xhr, status, error) {
      console.error("Error fetching items:", error);
      $("#items-list").html("<p style='color:red'>Failed to load items.</p>");
    });
  }

  $(document).on("click", ".edit-btn", function () {
    const row = $(this).closest("tr");
    const id = $(this).data("id");

    const name = row.find(".name").text();
    const description = row.find(".description").text();
    const price = row.find(".price").text();

    row
      .find(".name")
      .html(`<input type="text" class="edit-name" value="${name}">`);
    row
      .find(".description")
      .html(
        `<input type="text" class="edit-description" value="${description}">`
      );
    row
      .find(".price")
      .html(
        `<input type="number" step="0.01" class="edit-price" value="${price}">`
      );

    $(this).replaceWith(
      `<button class="update-btn" data-id="${id}">Update</button>`
    );
  });

  $(document).on("click", ".update-btn", function () {
    const row = $(this).closest("tr");
    const id = $(this).data("id");

    const formData = new FormData();
    formData.append("id", id);
    formData.append("name", row.find(".edit-name").val());
    formData.append("description", row.find(".edit-description").val());
    formData.append("price", row.find(".edit-price").val());

    $.ajax({
      url: "/cgi-bin/app.py?action=edit",
      method: "POST",
      data: formData,
      processData: false,
      contentType: false,
      success: function (res) {
        console.log("Update success:", res);
        fetchItems();
      },
      error: function (xhr, status, error) {
        console.error("Update failed:", error);
      },
    });
  });

  fetchItems();

  $("#add-item-form").submit(function (e) {
    e.preventDefault();
    const data = $(this).serialize();

    $.post(
      "/cgi-bin/app.py?action=add",
      data,
      function (res) {
        if (res.success) {
          fetchItems();
          $("#add-item-form")[0].reset();
          $("#add-item-form").hide();
        } else {
          alert("Error adding item: " + (res.error || "Unknown"));
        }
      },
      "json"
    ).fail(function (xhr, status, error) {
      alert("Request failed: " + error);
    });
  });

  let deleteItemId = null;

  $(document).on("click", ".delete-btn", function () {
    deleteItemId = $(this).data("id");
    $("#deleteModal").addClass("show"); // use class, not .show()
  });

  $("#cancelDelete").on("click", function () {
    deleteItemId = null;
    $("#deleteModal").removeClass("show"); // hide modal
  });

  $("#confirmDelete").on("click", function () {
    if (!deleteItemId) return;

    $.ajax({
      url: "/cgi-bin/app.py?action=delete",
      method: "POST",
      data: { id: deleteItemId }, // form encoded
      dataType: "json", // expect JSON
      success: function (res) {
        if (res.success) {
          console.log("Delete success:", res);
          $("#deleteModal").removeClass("show");
          fetchItems();
        } else {
          console.error("Delete failed:", res.error);
          alert(res.error);
        }
      },
      error: function (xhr, status, error) {
        console.error("Delete AJAX failed:", error, xhr.responseText);
      },
    });
  });
});
