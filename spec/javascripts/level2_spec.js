// Tests for level2.js


// Tests for converting between units:
describe("Unit conversions:", function() {

    // Use the following custom equality functions for these tests:
    beforeEach(function() {
        jasmine.addCustomEqualityTester(arrays_almost_equal);
    });

    it("to_ppm should take an array of ratios and convert to ppm",
            function() {
        var ratios = [0, 0.1, 1];
        var ppms = [0, 1e5, 1e6];
        expect(to_ppm(ratios)).toEqual(ppms);
    });

    it("to_kilo should take an array of heights i m and convert to km",
            function() {
        var meters = [0, 100, 10000];
        var kilometers = [0.0, 0.1, 10.0];
        expect(to_kilo(meters)).toEqual(kilometers);
    });

});


// Tests to validate input offset parameter:
describe("Checking if input is positive integer:", function() {

      it("returns true if input is positive integer",
              function() {
          var input = 10;
          expect(isPositiveInteger(input)).toEqual(true);
      });

      it("returns false if input is negative integer",
              function() {
          var input = -10;
          expect(isPositiveInteger(input)).toEqual(false);
      });

      it("returns false if input is float",
              function() {
          var input = 10.125;
          expect(isPositiveInteger(input)).toEqual(false);
      });

      it("returns false if input is string",
              function() {
          var input = 'abc';
          expect(isPositiveInteger(input)).toEqual(false);
      });

});


// Tests for getting input offset parameter:
describe("Get input  offset parameter:", function() {

      it("returns input if input is positive integer",
              function() {
          var input = 10;
          expect(getOffsetValue(input)).toEqual(10);
      });

      it("returns 0 if input is negative integer",
              function() {
          var input = -10;
          expect(getOffsetValue(input)).toEqual(0);
      });

      it("returns 0 if input is float",
              function() {
          var input = 10.125;
          expect(getOffsetValue(input)).toEqual(0);
      });

      it("returns 0 if input is string",
              function() {
          var input = 'abc';
          expect(getOffsetValue(input)).toEqual(0);
      });

});


// Functions for manipulating arrays for easier plotting:
describe("Tests for array manipulations for convenient plotting:",
        function() {

    // Use the following custom equality functions for these tests:
    beforeEach(function() {
        jasmine.addCustomEqualityTester(almost_equal);
    });

    it("find_max should add errors to data and find maximum",
            function() {
        errors = [0.1, 0.2, 0.1];
        data = [0.05, 0, -0.1];
        expect(find_max(data, errors)).toEqual(0.2);
    });

    it("find_min should subtract errors from data and find minimum",
            function() {
        errors = [0.1, 0.2, 0.2];
        data = [0.05, 0, -0.1];
        expect(find_min(data, errors)).toEqual(-0.3);
    });

    it("zip should combine arrays", function() {
        var first = [0, 1, 2];
        var second = [3, 4, 5];
        var third = [6, 7, 8];
        var zipped = zip([first, second, third]);
        var results = [[0, 3, 6], [1, 4, 7], [2, 5, 8]];

        for (var i=0; i < first.length; i ++) {
            expect(zipped[i]).toEqual(results[i]);
        }
    });

});

describe("Tests DOM manipulation for project selection", function() {

    beforeEach(function() {
        //jasmine.getFixtures().fixturesPath = '/home/martin/Devel/odin-api/spec/javascripts/fixtures';
        setFixtures('<select id="select-project" name="project"><option selected="selected" disabled>Choose project</option></select><div id="select-project-loader" class="loader"><div id="select-project-loader-spinner" class="spinner"></div><p>Loading projects...</p></div>');
    });

    it("adds success data", function() {

        var target = '#select-project';
        var settings = {
            target: target,
            itemKey: 'Name'
        };

        var data = {
            Data: [
                {
                    Name: 'Data 1'
                },
                {
                    Name: 'Data 2'
                }
            ]
        };

        populateSelectWithDataOrSetNoData(settings, data);

        expect($(target)).toContainText('Data 1');
        expect($(target)).toContainText('Data 2');
        expect($(target + " option").size()).toBe(3);
    });

    it("adds success data with title", function() {

        var target = '#select-project';
        var settings = {
            title: 'Title',
            target: target,
            itemKey: 'Name'
        };

        var data = {
            Data: [
                {
                    Name: 'Data 1'
                },
                {
                    Name: 'Data 2'
                }
            ]
        };

        populateSelectWithDataOrSetNoData(settings, data);

        expect($(target)).toContainText('Title');
        expect($(target)).toContainText('Data 1');
        expect($(target)).toContainText('Data 2');
        expect($(target + " option").size()).toBe(4);
    });

	it("adds no-data if no data", function() {

        var target = '#select-project';
        var settings = {
            empty: 'No data',
            target: target,
            itemKey: 'Name'
        };

        var data = {
            Data: [
            ]
        };

        populateSelectWithDataOrSetNoData(settings, data);

        expect($(target)).toContainText('No data');
        expect($(target + " option").size()).toBe(2);
	});

	it("adds fail if status code != 200", function() {

        var target = '#select-project';
        var settings = {
            fail: 'Error',
            target: target,
            itemKey: 'Name'
        };

        populateSelectWithFailMessage(settings);

        expect($(target)).toContainText('Error');
        expect($(target + " option").size()).toBe(2);
	});

	it("hides loader when single request is done", function() {

        var target = '#select-project';
        var targetLoader = '#select-project-loader';
        var settings = {
            loaderTarget: targetLoader,
        };

        var completeCheck = {
            single: true
        };
		$(targetLoader).show();
		expect($(targetLoader)).toBeVisible();
		handleSelectLoadingStatus(settings, completeCheck);
		expect($(targetLoader)).not.toBeVisible();
		expect($(target)).toBeVisible();

	});

	it("hides loader only when all requests are done", function() {

        var target = '#select-project';
        var targetLoader = '#select-project-loader';
        var settings = {
            loaderTarget: targetLoader,
            completionIndex: 0
        };

        var completeCheck = {
            single: false,
        	requestsEnded : [false, false]
        };
		$(targetLoader).show();
		expect($(targetLoader)).toBeVisible();

		handleSelectLoadingStatus(settings, completeCheck);

		expect($(targetLoader)).toBeVisible();
		expect($(target)).toBeVisible();

		settings.completionIndex = 1;

		handleSelectLoadingStatus(settings, completeCheck);

		expect($(targetLoader)).not.toBeVisible();
		expect($(target)).toBeVisible();
	});

});
